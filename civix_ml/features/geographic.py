"""
Geographic Features — built via DuckDB SQL joining CDRs to cell sectors.
Measures geographic spread and mobility of persons.
All features are point-in-time safe via `as_of_timestamp`.
"""
import duckdb
import pandas as pd
from pathlib import Path
from civix_ml.config import CDR_GLOB, CELL_GLOB
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection

log = get_logger(__name__)


def build_geographic_features(
    as_of_timestamp: str,
    output_path: Path,
    con: duckdb.DuckDBPyConnection | None = None,
) -> pd.DataFrame:
    """
    Build person-level geographic features from CDR + cell sector data.
    """
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    log.info(f"Building geographic features as_of={as_of_timestamp} ...")

    cdr_path  = CDR_GLOB.replace("\\", "/")
    cell_path = CELL_GLOB.replace("\\", "/")

    sql = f"""
    WITH cells AS (
        SELECT cell_id,
               centroid_latitude  AS lat,
               centroid_longitude AS lon,
               region
        FROM read_parquet('{cell_path}')
    ),
    cdr_loc AS (
        SELECT
            c.caller_person_id AS person_id,
            c.timestamp,
            c.cell_sector_id,
            cl.lat,
            cl.lon,
            cl.region,
            CAST(c.timestamp AS DATE) AS cdr_date
        FROM read_parquet('{cdr_path}', union_by_name=True, hive_partitioning=True) c
        JOIN cells cl ON cl.cell_id = c.cell_sector_id
        WHERE c.timestamp <= '{as_of_timestamp}'
          AND c.caller_person_id IS NOT NULL
    ),
    per_person AS (
        SELECT
            person_id,

            -- Unique locations
            COUNT(DISTINCT cell_sector_id)     AS unique_sectors,
            COUNT(DISTINCT region)             AS unique_regions,

            -- Home region = most frequently used region
            MODE() WITHIN GROUP (ORDER BY region) AS home_region,

            -- Geographic spread: approximate bounding box diagonal in degrees
            SQRT(
                POWER(MAX(lat) - MIN(lat), 2) +
                POWER(MAX(lon) - MIN(lon), 2)
            )                                  AS geo_spread_degrees,

            -- Standard deviation of location (movement entropy proxy)
            STDDEV(lat)                        AS lat_stddev,
            STDDEV(lon)                        AS lon_stddev,

            -- Cross-region calls ratio
            AVG(CASE WHEN region != (
                    SELECT MODE() WITHIN GROUP (ORDER BY region)
                    FROM cdr_loc cl2 WHERE cl2.person_id = cdr_loc.person_id
                ) THEN 1.0 ELSE 0.0 END)       AS cross_region_call_ratio,

            -- Active location days
            COUNT(DISTINCT cdr_date)           AS location_active_days

        FROM cdr_loc
        GROUP BY person_id
    )
    SELECT * FROM per_person
    """

    # cross_region_call_ratio correlated subquery can be slow — use a join approach
    simpler_sql = f"""
    WITH cells AS (
        SELECT cell_id,
               centroid_latitude  AS lat,
               centroid_longitude AS lon,
               region
        FROM read_parquet('{cell_path}')
    ),
    cdr_loc AS (
        SELECT
            c.caller_person_id AS person_id,
            c.cell_sector_id,
            cl.lat, cl.lon, cl.region,
            CAST(c.timestamp AS DATE) AS cdr_date
        FROM read_parquet('{cdr_path}', union_by_name=True, hive_partitioning=True) c
        JOIN cells cl ON cl.cell_id = c.cell_sector_id
        WHERE c.timestamp <= '{as_of_timestamp}'
          AND c.caller_person_id IS NOT NULL
    ),
    home_region AS (
        SELECT person_id, region AS home_reg,
               ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY cnt DESC) AS rn
        FROM (
            SELECT person_id, region, COUNT(*) AS cnt
            FROM cdr_loc GROUP BY person_id, region
        ) sub
    ),
    per_person AS (
        SELECT
            cl.person_id,
            COUNT(DISTINCT cl.cell_sector_id)                     AS unique_sectors,
            COUNT(DISTINCT cl.region)                             AS unique_regions,
            SQRT(POWER(MAX(cl.lat)-MIN(cl.lat),2)+POWER(MAX(cl.lon)-MIN(cl.lon),2))
                                                                  AS geo_spread_degrees,
            STDDEV(cl.lat)                                        AS lat_stddev,
            STDDEV(cl.lon)                                        AS lon_stddev,
            COUNT(DISTINCT cdr_date)                              AS location_active_days
        FROM cdr_loc cl
        GROUP BY cl.person_id
    )
    SELECT pp.*,
           hr.home_reg AS home_region,
           CASE WHEN pp.unique_regions > 0
                THEN (pp.unique_regions - 1.0) / pp.unique_regions
                ELSE 0 END                                        AS cross_region_ratio
    FROM per_person pp
    LEFT JOIN home_region hr ON hr.person_id = pp.person_id AND hr.rn = 1
    """

    df = con.execute(simpler_sql).df()
    log.info(f"  Done. {len(df):,} persons with geographic features.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(output_path), index=False, compression="snappy")
    log.info(f"  Saved to {output_path}")

    if close_con:
        con.close()

    return df
