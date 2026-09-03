import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
conn.autocommit = True
cur = conn.cursor()
with open('database/migrations/017_outbox_queue.sql', 'r') as f:
    sql = f.read()
    cur.execute(sql)
print("Migration 017 successfully applied via python script")
