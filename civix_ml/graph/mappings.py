"""
CIVIX Graph Mappings — Phase 3B
Builds and persists deterministic integer node index mappings for all entity types.
Mapping: original_entity_id (UUID string) -> integer node index (0-based)
Same input always produces same mapping (sorted, deterministic).
"""
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
from pathlib import Path
from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.graph.schema import GRAPH_MAPPINGS_DIR

log = get_logger(__name__)

# Entity source tables and their primary ID columns
_ENTITY_SOURCES = {
    "person":     (config.PERSONS_GLOB,  "person_id"),
    "phone":      (config.PHONES_GLOB,   "phone_id"),
    "sim":        (config.SIMS_GLOB,     "sim_id"),
    "device":     (config.DEVICES_GLOB,  "device_id"),
    "account":    (config.ACCOUNTS_GLOB, "account_id"),
    "cell_sector":(config.CELL_GLOB,     "cell_id"),
}


def build_mappings(force: bool = False) -> dict[str, Path]:
    """
    Build sorted, deterministic string→int mappings for all entity types.
    Returns dict of entity_type → Path to mapping parquet.
    """
    con = get_connection()
    paths = {}

    for entity, (glob, id_col) in _ENTITY_SOURCES.items():
        out_path = GRAPH_MAPPINGS_DIR / f"{entity}_mapping.parquet"
        if out_path.exists() and not force:
            log.info(f"  [skip] {entity} mapping already exists ({out_path})")
            paths[entity] = out_path
            continue

        log.info(f"  Building {entity} mapping from {glob} ...")
        glob_fwd = glob.replace("\\", "/")
        # Sort deterministically to guarantee same index every run
        df = con.execute(f"""
            SELECT DISTINCT {id_col} AS entity_id
            FROM read_parquet('{glob_fwd}')
            WHERE {id_col} IS NOT NULL
            ORDER BY {id_col}
        """).df()
        df["node_idx"] = range(len(df))
        tbl = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(tbl, str(out_path))
        log.info(f"  {entity}: {len(df):,} nodes → {out_path}")
        paths[entity] = out_path

    con.close()
    return paths


def load_mapping(entity: str) -> dict:
    """
    Load a mapping as {entity_id -> node_idx} dict.
    """
    path = GRAPH_MAPPINGS_DIR / f"{entity}_mapping.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Mapping not found: {path}. Run build_mappings() first.")
    tbl = pq.read_table(str(path))
    df  = tbl.to_pandas()
    return dict(zip(df["entity_id"], df["node_idx"]))


def load_mapping_df(entity: str):
    """Load a mapping as a DataFrame (entity_id, node_idx)."""
    path = GRAPH_MAPPINGS_DIR / f"{entity}_mapping.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Mapping not found: {path}. Run build_mappings() first.")
    return pq.read_table(str(path)).to_pandas()
