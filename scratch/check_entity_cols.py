import psycopg2

def check():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='entity';")
    print(cur.fetchall())
    conn.close()

if __name__ == '__main__':
    check()
