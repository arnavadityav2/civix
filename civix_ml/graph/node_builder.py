"""
CIVIX Graph Node Builder — Phase 3B
Extracts and materialises all graph nodes with their attributes.
Writes one Parquet file per node type to graph_artifacts/nodes/.
"""
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.graph.schema import GRAPH_NODES_DIR

log = get_logger(__name__)


def build_all_nodes(force: bool = False) -> dict[str, Path]:
    """Build all node tables from Profile C entity Parquets."""
    con = get_connection()
    paths = {}

    _builds = [
        ("person", config.PERSONS_GLOB.replace("\\", "/"),
         "person_id AS node_id, gender, occupation, dob AS date_of_birth"),
        ("phone", config.PHONES_GLOB.replace("\\", "/"),
         "phone_id AS node_id, number_masked"),
        ("sim", config.SIMS_GLOB.replace("\\", "/"),
         "sim_id AS node_id, operator, is_active"),
        ("device", config.DEVICES_GLOB.replace("\\", "/"),
         "device_id AS node_id, brand, device_type"),
        ("account", config.ACCOUNTS_GLOB.replace("\\", "/"),
         "account_id AS node_id, primary_holder_id, account_type"),
        ("cell_sector", config.CELL_GLOB.replace("\\", "/"),
         "cell_id AS node_id, centroid_latitude, centroid_longitude, region"),
    ]

    for entity, glob, select_expr in _builds:
        out = GRAPH_NODES_DIR / f"{entity}_nodes.parquet"
        if out.exists() and not force:
            log.info(f"  [skip] {entity} nodes exist at {out}")
            paths[entity] = out
            continue
        log.info(f"  Building {entity} nodes ...")
        df = con.execute(f"SELECT {select_expr} FROM read_parquet('{glob}')").df()
        pq.write_table(pa.Table.from_pandas(df, preserve_index=False), str(out))
        log.info(f"  {entity}: {len(df):,} nodes → {out}")
        paths[entity] = out

    con.close()
    return paths
