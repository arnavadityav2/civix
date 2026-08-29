import torch
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path

from civix_ml import config
from civix_ml.graph.schema import GRAPH_FEATURES_DIR, GRAPH_MAPPINGS_DIR, GRAPH_EDGES_DIR
from civix_ml.models.graph_baselines import load_graph_features
from civix_ml.utils.duckdb_utils import get_connection

print("Loading data for GNN evaluation...")

X_train, y_train, _ = load_graph_features("TRAIN")
X_val,   y_val,   _ = load_graph_features("VALIDATION")
X_test,  y_test,  _ = load_graph_features("TEST")

phone_map_df = pq.read_table(str(GRAPH_MAPPINGS_DIR / "phone_mapping.parquet")).to_pandas()
person_map_df = pq.read_table(str(GRAPH_MAPPINGS_DIR / "person_mapping.parquet")).to_pandas()

cdr_agg_path = str(GRAPH_EDGES_DIR / "cdr_aggregated" / "cdr_aggregated.parquet")
edges_raw = pq.read_table(cdr_agg_path).to_pandas()[["src", "dst"]]

phone_to_idx = dict(zip(phone_map_df["entity_id"], phone_map_df["node_idx"]))
edges_raw["src_node_idx"] = edges_raw["src"].map(phone_to_idx)
edges_raw["dst_node_idx"] = edges_raw["dst"].map(phone_to_idx)
edges_raw = edges_raw.dropna(subset=["src_node_idx", "dst_node_idx"])
edges_raw = edges_raw.astype({"src_node_idx": int, "dst_node_idx": int})

person_to_idx = dict(zip(person_map_df["entity_id"], person_map_df["node_idx"]))
all_persons_df = pd.concat([
    X_train.assign(split="TRAIN"),
    X_val.assign(split="VALIDATION"),
    X_test.assign(split="TEST"),
], ignore_index=True)

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

test_mask  = torch.tensor(full_df["split"].values == "TEST", dtype=torch.bool)
labels     = torch.tensor(full_df["is_positive_label"].astype(int).values, dtype=torch.long)

x = torch.tensor(node_feats.values, dtype=torch.float32)

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
person_edges = person_edges.dropna(subset=["src_pidx", "dst_pidx"])
person_edges = person_edges.drop_duplicates(subset=["src_pidx", "dst_pidx"])
person_edges = person_edges.astype({"src_pidx": int, "dst_pidx": int})

edge_index = torch.tensor(
    person_edges[["src_pidx", "dst_pidx"]].values.T, dtype=torch.long
)

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

y_test = labels[test_mask].numpy()
probs_test = probs[test_mask]

from civix_ml.evaluation.metrics import evaluate
metrics = evaluate(y_test, probs_test, model_name="graphsage_test", threshold=0.5)
print("--- FINAL GNN TEST METRICS ---")
for k, v in metrics.items():
    print(f"{k}: {v}")
