"""DuckDB connection factory with D: drive temp dir and memory tuning."""
import duckdb
from civix_ml import config


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Create a DuckDB in-memory connection configured to:
    - spill temp files to D: drive (C: is nearly full)
    - allow unlimited temp spill
    - reduce threads to 2 (lowest peak memory)
    - disable insertion-order preservation (halves sort memory)
    """
    con = duckdb.connect(
        database=":memory:",
        config={
            "temp_directory": config.DUCKDB_TEMP_DIR,
            "memory_limit":   config.DUCKDB_MEMORY_LIMIT,
            "threads":        config.DUCKDB_THREADS,
            "preserve_insertion_order": False,
        }
    )
    # Also set the max temp size to be generous — use D: drive space
    con.execute("PRAGMA max_temp_directory_size='100GiB'")
    return con
