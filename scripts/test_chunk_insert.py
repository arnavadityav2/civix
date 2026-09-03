import duckdb
from neo4j import GraphDatabase

con = duckdb.connect(":memory:")
cdr_path = "demo_world_15k_output/cdrs/**/*.parquet"
tuples = con.execute(f"""
    SELECT caller_phone_id::TEXT, callee_phone_id::TEXT, COUNT(*)::INT
    FROM read_parquet('{cdr_path}')
    WHERE caller_phone_id IS NOT NULL AND callee_phone_id IS NOT NULL
    GROUP BY caller_phone_id, callee_phone_id
    LIMIT 10
""").fetchall()
con.close()

print("Tuples:", tuples)

driver = GraphDatabase.driver("bolt://localhost:7688", auth=None)
with driver.session() as s:
    batch = [{"src": r[0], "dst": r[1], "cnt": r[2]} for r in tuples]
    res = s.run("""
        UNWIND $batch AS row
        OPTIONAL MATCH (src:PhoneNumber {entity_id: row.src})
        OPTIONAL MATCH (dst:PhoneNumber {entity_id: row.dst})
        RETURN row.src, src IS NOT NULL AS src_found, row.dst, dst IS NOT NULL AS dst_found
    """, batch=batch).data()
    print("Match Diagnostic:", res)
driver.close()
