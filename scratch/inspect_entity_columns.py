import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("POSTGRES_DB", "civix_demo")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

for table in ['person', 'organization', 'vehicle', 'device', 'phone_number']:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = '{table}'")
    cols = [r[0] for r in cur.fetchall()]
    print(f"Table {table} columns:", cols)

cur.close()
conn.close()
