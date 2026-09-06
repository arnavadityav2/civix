import psycopg2

try:
    conn = psycopg2.connect(
        dbname="civix_demo",
        user="postgres",
        password="password",
        host="127.0.0.1",
        port=5432,
        connect_timeout=3
    )
    cur = conn.cursor()
    cur.execute("SELECT current_setting('data_directory'), count(*) FROM information_schema.tables WHERE table_schema='civix';")
    data_dir, tbl_count = cur.fetchone()
    print(f"PostgreSQL 17 Connected! Data Directory: {data_dir} | CIVIX Table Count: {tbl_count}")
    cur.close()
    conn.close()
except Exception as e:
    try:
        conn = psycopg2.connect(
            dbname="civix_demo",
            user="postgres",
            password="postgres",
            host="127.0.0.1",
            port=5432,
            connect_timeout=3
        )
        cur = conn.cursor()
        cur.execute("SELECT current_setting('data_directory'), count(*) FROM information_schema.tables WHERE table_schema='civix';")
        data_dir, tbl_count = cur.fetchone()
        print(f"PostgreSQL 17 Connected! Data Directory: {data_dir} | CIVIX Table Count: {tbl_count}")
        cur.close()
        conn.close()
    except Exception as e2:
        print(f"PostgreSQL 17 Connection Error: {e2}")
