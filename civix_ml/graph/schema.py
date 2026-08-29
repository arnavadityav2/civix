"""
CIVIX Graph Schema Definitions — Phase 3B
Defines node types, edge types, and their source tables.
All definitions must match what actually exists in Profile C.
No invented relationships.
"""

# ── Node types (only those with data in Profile C) ──────────────────────────
NODE_TYPES = [
    "Person",    # 250,000 — persons/*.parquet
    "Phone",     # ~500,000 — phones/*.parquet
    "SIM",       # ~350,000 — sims/*.parquet
    "Device",    # ~350,000 — devices/*.parquet
    "Account",   # ~350,000 — accounts/*.parquet
    "CellSector",# ~8,000   — cell_sectors/*.parquet
    "Case",      # ~25,000  — cases/*.parquet
]

# ── Edge types ────────────────────────────────────────────────────────────────
# Each edge is defined as: (source_type, relation, target_type, source_table)
EDGE_TYPES = [
    # Temporal / transactional edges
    ("Phone",   "CALLED",        "Phone",   "cdrs"),
    ("Account", "TRANSFERRED_TO","Account", "transactions"),
    # Ownership / association edges
    ("Person",  "OWNS",          "Phone",   "phones"),
    ("Person",  "USES",          "SIM",     "sims"),
    ("Person",  "USES",          "Device",  "devices"),
    ("Person",  "OWNS",          "Account", "accounts"),
    ("Person",  "INVOLVED_IN",   "Case",    "case_roles"),
    ("Phone",   "LOCATED_AT",    "CellSector", "cdrs"),  # via CDR cell_sector_id
]

# ── Graph artifact output directory ─────────────────────────────────────────
import os
from pathlib import Path
base_dir = os.environ.get("CIVIX_PROFILE_DIR", r"D:\civix_data\synthetic\profile_v2_v2a")
GRAPH_DIR = Path(base_dir) / "graph_artifacts"
GRAPH_NODES_DIR    = GRAPH_DIR / "nodes"
GRAPH_EDGES_DIR    = GRAPH_DIR / "edges"
GRAPH_MAPPINGS_DIR = GRAPH_DIR / "mappings"
GRAPH_FEATURES_DIR = GRAPH_DIR / "features"
GRAPH_SPLITS_DIR   = GRAPH_DIR / "splits"
GRAPH_META_DIR     = GRAPH_DIR / "metadata"

for _d in [GRAPH_NODES_DIR, GRAPH_EDGES_DIR, GRAPH_MAPPINGS_DIR,
           GRAPH_FEATURES_DIR, GRAPH_SPLITS_DIR, GRAPH_META_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
