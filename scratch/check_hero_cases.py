import psycopg2

def main():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute("""
        SELECT case_id, case_number, title, priority, status, created_at 
        FROM civix.investigative_case 
        WHERE case_number NOT LIKE 'SYN-%' 
        ORDER BY created_at DESC;
    """)
    rows = cur.fetchall()
    print(f"Total Golden/Hero cases found: {len(rows)}")
    for r in rows:
        print(f"ID: {r[0]} | NUM: {r[1]} | TITLE: {r[2]}")
    conn.close()

if __name__ == "__main__":
    main()
