"""Check cardinality of categorical columns in feature matrix."""
import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")
from civix_ml.utils.duckdb_utils import get_connection

con = get_connection()
feat = "D:/civix_data/synthetic/profile_c/features_v1/features_merged.parquet"

r = con.execute(f"""
    SELECT
        COUNT(DISTINCT gender) AS gender_card,
        COUNT(DISTINCT occupation) AS occ_card,
        COUNT(DISTINCT home_region) AS home_region_card
    FROM read_parquet('{feat}')
""").fetchone()
print(f"gender cardinality  : {r[0]}")
print(f"occupation cardinality: {r[1]}")
print(f"home_region cardinality: {r[2]}")

# Top 10 genders
genders = con.execute(f"SELECT gender, COUNT(*) as n FROM read_parquet('{feat}') GROUP BY gender ORDER BY n DESC").fetchall()
print(f"\nGender values: {genders}")

occ = con.execute(f"SELECT occupation, COUNT(*) as n FROM read_parquet('{feat}') GROUP BY occupation ORDER BY n DESC LIMIT 5").fetchall()
print(f"\nTop 5 occupations: {occ}")
con.close()
