import psycopg2

def test_sql():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute("""
        WITH enriched_cases AS (
            SELECT 
                c.case_id,
                c.case_number,
                c.title,
                GREATEST(c.updated_at, c.created_at) as last_activity_at,
                CASE WHEN c.case_number LIKE 'SYN-%' THEN 'SYNTHETIC' ELSE 'GOLDEN' END as provenance
            FROM civix.investigative_case c
        )
        SELECT case_number, title, provenance
        FROM enriched_cases c
        ORDER BY 
            (CASE WHEN c.provenance = 'GOLDEN' THEN 0 ELSE 1 END) ASC,
            last_activity_at DESC
        LIMIT 15;
    """)
    rows = cur.fetchall()
    print("SQL QUERY DIRECT OUTPUT:")
    for i, r in enumerate(rows):
        print(f"{i+1:2d}. [{r[2]}] {r[0]} | {r[1]}")
    conn.close()

if __name__ == '__main__':
    test_sql()
