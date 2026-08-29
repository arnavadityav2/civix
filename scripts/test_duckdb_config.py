from civix_ml.utils.duckdb_utils import get_connection
con = get_connection()
r = con.execute("SELECT 1+1 AS ok").fetchone()
settings = con.execute("SELECT current_setting('temp_directory'), current_setting('memory_limit')").fetchone()
print("DuckDB OK:", r)
print("temp_dir :", settings[0])
print("mem_limit:", settings[1])
con.close()
print("All good.")
