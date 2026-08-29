"""
CIVIX GraphSAGE GNN — Phase 5 Controlled Experiment 2
Implements GraphSAGE with Feature Scaling, LayerNorm, Class Weighting, and Gradient Clipping.
Designed for Dell G15 (16GB RAM, RTX 3050 6GB).
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch import Tensor

# PyTorch Geometric imports — lazy so the module can be imported even if PyG not installed
try:
    from torch_geometric.nn import SAGEConv
    from torch_geometric.data import Data
    from torch_geometric.loader import NeighborLoader
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False

from civix_ml.utils import get_logger

log = get_logger(__name__)


@dataclass
class GraphSAGEConfig:
    hidden_channels: int = 64
    num_layers:      int = 2
    dropout:         float = 0.3
    lr:              float = 5e-4
    epochs:          int = 30
    batch_size:      int = 250000
    fanout:          list[int] = field(default_factory=lambda: [15, 10])
    device:          str = "auto"
    seed:            int = 42
    patience:        int = 10      # early stopping patience
    num_workers:     int = 0       # safer for Windows

    def resolve_device(self) -> torch.device:
        if self.device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(self.device)


class GraphSAGEModel(torch.nn.Module):
    """
    GraphSAGE for node classification with LayerNorm for numerical stability.
    """
    def __init__(self, in_channels: int, hidden_channels: int,
                 out_channels: int, num_layers: int, dropout: float):
        super().__init__()
        self.dropout = dropout
        self.convs = torch.nn.ModuleList()
        self.norms = torch.nn.ModuleList()
        
        self.convs.append(SAGEConv(in_channels, hidden_channels))
        self.norms.append(torch.nn.LayerNorm(hidden_channels))
        
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels))
            self.norms.append(torch.nn.LayerNorm(hidden_channels))
            
        self.convs.append(SAGEConv(hidden_channels, out_channels))

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = self.norms[i](x)
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        return x


def build_pyg_data(
    features_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    labels_series: pd.Series | None,
    src_col: str = "src_node_idx",
    dst_col: str = "dst_node_idx",
) -> "Data":
    """
    Build a PyTorch Geometric Data object from DataFrames.
    """
    if not PYG_AVAILABLE:
        raise ImportError("torch_geometric is not installed. Run: pip install torch_geometric")

    feat_cols = [c for c in features_df.columns if c != "node_idx"]
    x = torch.tensor(features_df[feat_cols].values, dtype=torch.float32)
    edge_index = torch.tensor(
        edges_df[[src_col, dst_col]].values.T,
        dtype=torch.long
    )

    data = Data(x=x, edge_index=edge_index)
    if labels_series is not None:
        data.y = torch.tensor(labels_series.values, dtype=torch.long)

    return data


def train_graphsage(
    data:        "Data",
    train_mask:  Tensor,
    val_mask:    Tensor,
    cfg:         GraphSAGEConfig,
    model_dir:   Path,
) -> dict:
    """
    Train GraphSAGE numerically stabilized with DropEdge, Scaling, and Weights.
    """
    if not PYG_AVAILABLE:
        raise ImportError("torch_geometric is not installed.")

    device = cfg.resolve_device()
    log.info(f"GraphSAGE training on device={device}")
    log.info(f"  Config: {cfg}")
    
    # User-requested memory and topology tracking
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        ram_gb = psutil.virtual_memory().available / (1024**3)
        graph_mem_mb = (data.x.element_size() * data.x.nelement() + data.edge_index.element_size() * data.edge_index.nelement()) / (1024**2)
        log.info(f"  Nodes: {data.num_nodes:,}")
        log.info(f"  Edges: {data.num_edges:,}")
        log.info(f"  Node feature dimensions: {data.num_node_features}")
        log.info(f"  Estimated raw graph memory: {graph_mem_mb:.2f} MB")
        log.info(f"  Available RAM: {ram_gb:.2f} GB")
        log.info(f"  Training mode: FULL-BATCH (Documented Deviation)")
    except ImportError:
        log.info(f"  Graph: {data.num_nodes:,} nodes, {data.num_edges:,} edges")

    # Subsample edges if they exceed 5 million to prevent OOM in full-batch fallback
    MAX_EDGES = 5_000_000
    if data.edge_index.shape[1] > MAX_EDGES:
        import logging
        seed_val = 42
        logging.getLogger(__name__).warning(
            f"EXPERIMENTAL DEVIATION: GraphSAGE — CPU, full-batch, 5M-edge static DropEdge subsampling, "
            f"250K nodes, 30 epochs. Seed: {seed_val}. Original edges: {data.edge_index.shape[1]:,} -> {MAX_EDGES:,}"
        )
        torch.manual_seed(seed_val)
        perm = torch.randperm(data.edge_index.shape[1])[:MAX_EDGES]
        data.edge_index = data.edge_index[:, perm]

    # Deterministic seed
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)

    data.train_mask = train_mask
    data.val_mask = val_mask
    
    model_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # EXPERIMENT 2 STABILIZATIONS
    # ---------------------------------------------------------
    
    # 1. Handle NaNs/Infs
    data.x = torch.nan_to_num(data.x, nan=0.0, posinf=1e6, neginf=-1e6)
    
    # 2. Fit Scaler ONLY on Training Nodes
    train_x = data.x[data.train_mask]
    train_mean = train_x.mean(dim=0, keepdim=True)
    train_std = train_x.std(dim=0, keepdim=True)
    
    zero_var_count = (train_std == 0).sum().item()
    log.info(f"  Feature scaling: Found {zero_var_count} zero-variance features.")
    train_std[train_std == 0] = 1.0 # prevent div by zero
    
    # 3. Transform ALL nodes
    data.x = (data.x - train_mean) / train_std
    log.info(f"  Scaled features max abs value: {data.x.abs().max().item():.4f}")
    torch.save({"mean": train_mean, "std": train_std}, model_dir / "scaler.pt")
    
    # 4. Class Imbalance Weighting ONLY from Training Labels
    train_y = data.y[data.train_mask]
    pos_count = (train_y == 1).sum().item()
    neg_count = (train_y == 0).sum().item()
    pos_weight = neg_count / max(1, pos_count)
    log.info(f"  Class Weighting: {neg_count} Neg / {pos_count} Pos -> Positive Weight: {pos_weight:.4f}")

    n_classes = int(data.y.max().item()) + 1 if data.y is not None else 2

    model = GraphSAGEModel(
        in_channels=data.num_node_features,
        hidden_channels=cfg.hidden_channels,
        out_channels=n_classes,
        num_layers=cfg.num_layers,
        dropout=cfg.dropout,
    ).to(device)

    data = data.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    
    # Apply class weights to loss
    weights = torch.tensor([1.0, pos_weight], dtype=torch.float32).to(device)
    criterion = torch.nn.CrossEntropyLoss(weight=weights)

    log.info(f"  Starting stabilized training for up to {cfg.epochs} epochs ...")
    best_val_loss = float("inf")
    patience_counter = 0
    history = []

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        
        # Check for NaN logits
        if torch.isnan(out).any() or torch.isinf(out).any():
            log.error(f"NaN/Inf logits detected at epoch {epoch}! Stopping training.")
            break
            
        loss = criterion(out[data.train_mask], data.y[data.train_mask])
        loss.backward()
        
        # Gradient Clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        train_loss = loss.item()

        # Validation
        model.eval()
        with torch.no_grad():
            out_val = model(data.x, data.edge_index)
            val_loss = criterion(out_val[data.val_mask], data.y[data.val_mask]).item()
            
            # Count positive predictions on val
            val_probs = torch.softmax(out_val[data.val_mask], dim=1)[:, 1]
            val_preds = (val_probs > 0.5).sum().item()

        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss, "val_pos_preds": val_preds})

        if epoch % 5 == 0 or epoch == 1:
            log.info(f"    Epoch {epoch:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Pos Preds: {val_preds}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), model_dir / "graphsage_best.pt")
        else:
            patience_counter += 1

        if patience_counter >= cfg.patience:
            log.info(f"  Early stopping at epoch {epoch}")
            break

    # Save training config + history
    (model_dir / "graphsage_config.json").write_text(
        json.dumps({"config": cfg.__dict__, "history": history}, indent=2)
    )
    
    try:
        peak_mem_mb = process.memory_info().peak_wset / (1024**2)
        log.info(f"  Peak/observed memory: {peak_mem_mb:.2f} MB")
    except Exception:
        pass
        
    log.info(f"  Best model saved → {model_dir / 'graphsage_best.pt'}")
    return {"best_val_loss": best_val_loss, "history": history}
