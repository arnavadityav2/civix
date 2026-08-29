import torch
import pandas as pd
import numpy as np
from pathlib import Path

from civix_ml import config
from civix_ml.graph.schema import GRAPH_FEATURES_DIR, GRAPH_MAPPINGS_DIR
from civix_ml.models.graph_baselines import load_graph_features
from civix_ml.utils.duckdb_utils import get_connection

print("=== DIAGNOSTIC AUDIT: GraphSAGE Run 1 ===")

# 1. Load Data
X_train, y_train, _ = load_graph_features("TRAIN")
X_val,   y_val,   _ = load_graph_features("VALIDATION")
X_test,  y_test,  _ = load_graph_features("TEST")

import pyarrow.parquet as pq
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
test_mask = torch.tensor(full_df["split"].values == "TEST", dtype=torch.bool)
train_mask = torch.tensor(full_df["split"].values == "TRAIN", dtype=torch.bool)

print("\n--- 1. Label Distribution ---")
pos_train = labels[train_mask].sum().item()
tot_train = train_mask.sum().item()
print(f"Train Positive Class Ratio: {pos_train}/{tot_train} ({pos_train/tot_train*100:.2f}%)")
pos_test = labels[test_mask].sum().item()
tot_test = test_mask.sum().item()
print(f"Test Positive Class Ratio: {pos_test}/{tot_test} ({pos_test/tot_test*100:.2f}%)")

print("\n--- 2. Node Feature (x) Scales ---")
print(f"Min:  {x.min().item():.4f}")
print(f"Max:  {x.max().item():.4f}")
print(f"Mean: {x.mean().item():.4f}")
print(f"Std:  {x.std().item():.4f}")
print("Example Max per column:")
maxes = x.max(dim=0)[0].numpy()
for i, col in enumerate(feat_cols[:5]):
    print(f"  {col}: {maxes[i]:.2f}")

# 3. Model Output Analysis
print("\n--- 3. Logits and Probabilities Analysis ---")
# Build a dummy edge index (we just want to see the model output, but we need edges for GraphSAGE)
# We will just reuse the fast edge loader from eval
cdr_agg_path = str(Path(config.DATA_DIR) / "synthetic/profile_c/graph_artifacts/edges/cdr_aggregated/cdr_aggregated.parquet")
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

# Apply exact 5M sample
MAX_EDGES = 5_000_000
if edge_index.shape[1] > MAX_EDGES:
    torch.manual_seed(42)
    perm = torch.randperm(edge_index.shape[1])[:MAX_EDGES]
    edge_index = edge_index[:, perm]

from civix_ml.models.gnn import GraphSAGEModel
model = GraphSAGEModel(in_channels=25, hidden_channels=64, out_channels=2, num_layers=2, dropout=0.3)
model_path = r"D:\civix_data\models\registry\graphsage_20260829T211318\graphsage_best.pt"
model.load_state_dict(torch.load(model_path, weights_only=True))
model.eval()
with torch.no_grad():
    out = model(x, edge_index)
    probs = torch.softmax(out, dim=1)[:, 1].numpy()

test_logits = out[test_mask].numpy()
test_probs = probs[test_mask]

print(f"Test Logits - Min: {test_logits.min():.4f}, Max: {test_logits.max():.4f}, Mean: {test_logits.mean():.4f}, Std: {test_logits.std():.4f}")
print(f"Unique Probabilities count: {len(np.unique(test_probs))}")
print(f"Sample Probabilities: {test_probs[:5]}")
