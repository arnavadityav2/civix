import torch
import pandas as pd
import numpy as np
from pathlib import Path
import pyarrow.parquet as pq

from civix_ml import config
from civix_ml.graph.schema import GRAPH_FEATURES_DIR, GRAPH_MAPPINGS_DIR, GRAPH_EDGES_DIR
from civix_ml.models.graph_baselines import load_graph_features
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.models.gnn import GraphSAGEConfig, train_graphsage, GraphSAGEModel
from civix_ml.evaluation.metrics import evaluate

print("==================================================")
print("CIVIX PHASE 5 — CONTROLLED GNN EXPERIMENT 2")
print("==================================================")

# 1. LOAD DATA (EXACT SAME AS EXPERIMENT 1)
print("Loading exact training and evaluation sets...")
X_train, y_train, _ = load_graph_features("TRAIN")
X_val,   y_val,   _ = load_graph_features("VALIDATION")
X_test,  y_test,  _ = load_graph_features("TEST")

person_map_df = pq.read_table(str(GRAPH_MAPPINGS_DIR / "person_mapping.parquet")).to_pandas()
person_to_idx = dict(zip(person_map_df["entity_id"], person_map_df["node_idx"]))

con = get_connection()
feat_path = str(GRAPH_FEATURES_DIR / "graph_features.parquet").replace("\\", "/")
labs_path = config.LABELS_GLOB.replace("\\", "/")
splits_path = config.SPLITS_GLOB.replace("\\", "/")
full_df = con.execute(f"""
    SELECT g.person_id, g.* EXCLUDE(person_id),
           l.is_positive_label, s.split
    FROM read_parquet('{feat_path}') g
    JOIN read_parquet('{splits_path}') s ON s.entity_id = g.person_id
    JOIN read_parquet('{labs_path}') l ON l.entity_id = g.person_id
""").df()
con.close()

full_df["node_idx"] = full_df["person_id"].map(person_to_idx)
full_df = full_df.dropna(subset=["node_idx"]).sort_values("node_idx")
feat_cols = [c for c in X_train.columns]
node_feats = full_df[feat_cols].fillna(0)

x = torch.tensor(node_feats.values, dtype=torch.float32)
labels = torch.tensor(full_df["is_positive_label"].astype(int).values, dtype=torch.long)
train_mask = torch.tensor(full_df["split"].values == "TRAIN", dtype=torch.bool)
val_mask = torch.tensor(full_df["split"].values == "VALIDATION", dtype=torch.bool)
test_mask = torch.tensor(full_df["split"].values == "TEST", dtype=torch.bool)

cdr_agg_path = str(GRAPH_EDGES_DIR / "cdr_aggregated" / "cdr_aggregated.parquet")
edges_raw = pq.read_table(cdr_agg_path).to_pandas()[["src", "dst"]]
phone_map_df = pq.read_table(str(GRAPH_MAPPINGS_DIR / "phone_mapping.parquet")).to_pandas()
phone_to_idx = dict(zip(phone_map_df["entity_id"], phone_map_df["node_idx"]))
edges_raw["src_node_idx"] = edges_raw["src"].map(phone_to_idx)
edges_raw["dst_node_idx"] = edges_raw["dst"].map(phone_to_idx)
edges_raw = edges_raw.dropna(subset=["src_node_idx", "dst_node_idx"])
edges_raw = edges_raw.astype({"src_node_idx": int, "dst_node_idx": int})

con2 = get_connection()
cdrs_g = config.CDR_GLOB.replace("\\", "/")
phone_person = con2.execute(f"""
    SELECT DISTINCT caller_phone_id AS phone_id, caller_person_id AS person_id 
    FROM read_parquet('{cdrs_g}')
    WHERE caller_person_id IS NOT NULL
""").df()
con2.close()
pp_map = dict(zip(phone_person["phone_id"], phone_person["person_id"]))
edges_raw["src_person_id"] = edges_raw["src"].map(pp_map)
edges_raw["dst_person_id"] = edges_raw["dst"].map(pp_map)
person_edges = edges_raw.dropna(subset=["src_person_id", "dst_person_id"])
person_edges["src_pidx"] = person_edges["src_person_id"].map(person_to_idx)
person_edges["dst_pidx"] = person_edges["dst_person_id"].map(person_to_idx)
person_edges = person_edges.dropna(subset=["src_pidx", "dst_pidx"]).drop_duplicates(subset=["src_pidx", "dst_pidx"]).astype({"src_pidx": int, "dst_pidx": int})
edge_index = torch.tensor(person_edges[["src_pidx", "dst_pidx"]].values.T, dtype=torch.long)

from torch_geometric.data import Data
data = Data(x=x, edge_index=edge_index, y=labels)

print("\n==================================================")
print("STEP 5: SANITY CHECK (2 Epochs)")
print("==================================================")
model_dir = Path(config.MODELS_DIR) / "registry" / "gnn_experiment_2"

# Run 2 epochs
cfg_sanity = GraphSAGEConfig(device="cpu", epochs=2)
# We need to manually clone data because train_graphsage modifies data.x and data.edge_index in place
data_sanity = data.clone()
result_sanity = train_graphsage(data_sanity, train_mask, val_mask, cfg_sanity, model_dir / "sanity")

# Check model output for NaNs, Infs, and unique predictions
model_sanity = GraphSAGEModel(25, 64, 2, 2, 0.3)
model_sanity.load_state_dict(torch.load(model_dir / "sanity" / "graphsage_best.pt", weights_only=True))
model_sanity.eval()
with torch.no_grad():
    out_sanity = model_sanity(data_sanity.x, data_sanity.edge_index)
    probs_sanity = torch.softmax(out_sanity, dim=1)[:, 1].numpy()

if torch.isnan(out_sanity).any() or torch.isinf(out_sanity).any():
    print("SANITY CHECK FAILED: NaN or Inf logits detected.")
    exit(1)

unique_preds = len(np.unique(probs_sanity))
print(f"Logits range: [{out_sanity.min():.4f}, {out_sanity.max():.4f}]")
print(f"Unique probabilities count: {unique_preds}")

if unique_preds <= 2:
    print("SANITY CHECK FAILED: Model still collapsed to constant predictions.")
    exit(1)

print("SANITY CHECK PASSED: Logits are finite and varied.")


print("\n==================================================")
print("STEP 6: FULL 30-EPOCH EXPERIMENT 2")
print("==================================================")
cfg_full = GraphSAGEConfig(device="cpu", epochs=30)
data_full = data.clone()
result_full = train_graphsage(data_full, train_mask, val_mask, cfg_full, model_dir / "full")

print("\n==================================================")
print("STEP 7: UNTOUCHED TEST EVALUATION")
print("==================================================")
model_full = GraphSAGEModel(25, 64, 2, 2, 0.3)
model_full.load_state_dict(torch.load(model_dir / "full" / "graphsage_best.pt", weights_only=True))
model_full.eval()
with torch.no_grad():
    out_full = model_full(data_full.x, data_full.edge_index)
    probs_full = torch.softmax(out_full, dim=1)[:, 1].numpy()

test_y = data_full.y[test_mask].numpy()
test_probs = probs_full[test_mask]

metrics = evaluate(test_y, test_probs, model_name="graphsage_exp2", threshold=0.5)

print("\n--- EXPERIMENT 2 TEST METRICS ---")
for k, v in metrics.items():
    print(f"{k}: {v}")
    
# Collapse Detection
if metrics["pr_auc"] < 0.11 and metrics["roc_auc"] < 0.51:
    print("\nCOLLAPSE DETECTED: The model failed to lift above the random baseline.")
else:
    print("\nSUCCESS: The model extracted meaningful signal above the baseline!")
