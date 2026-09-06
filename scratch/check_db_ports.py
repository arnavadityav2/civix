import socket
import psycopg2
from neo4j import GraphDatabase

def check_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

print("=== PORT CONNECTIVITY CHECK ===")
pg_5432 = check_port("127.0.0.1", 5432)
print(f"Port 5432 (PostgreSQL 17): {'OPEN' if pg_5432 else 'CLOSED'}")

neo_7688 = check_port("127.0.0.1", 7688)
print(f"Port 7688 (Neo4j Bolt): {'OPEN' if neo_7688 else 'CLOSED'}")

neo_7687 = check_port("127.0.0.1", 7687)
print(f"Port 7687 (Neo4j Default Bolt): {'OPEN' if neo_7687 else 'CLOSED'}")

neo_7475 = check_port("127.0.0.1", 7475)
print(f"Port 7475 (Neo4j HTTP): {'OPEN' if neo_7475 else 'CLOSED'}")

print("\n=== DATABASE AUTH & PING CHECK ===")
# Check PostgreSQL Connection
if pg_5432:
    try:
        conn = psycopg2.connect(
            dbname="civix_demo",
            user="postgres",
            password="password", # or default password
            host="127.0.0.1",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT version(), current_setting('data_directory');")
        version, data_dir = cur.fetchone()
        cur.close()
        conn.close()
        print(f"PostgreSQL 17 PING SUCCESS! Data directory: {data_dir}")
    except Exception as e:
        # Try with password 'postgres'
        try:
            conn = psycopg2.connect(
                dbname="civix_demo",
                user="postgres",
                password="postgres",
                host="127.0.0.1",
                port=5432
            )
            cur = conn.cursor()
            cur.execute("SELECT version(), current_setting('data_directory');")
            version, data_dir = cur.fetchone()
            cur.close()
            conn.close()
            print(f"PostgreSQL 17 PING SUCCESS! Data directory: {data_dir}")
        except Exception as e2:
            print(f"PostgreSQL 17 PING FAILED: {e2}")
else:
    print("PostgreSQL 17 is NOT listening on port 5432.")

# Check Neo4j Connection
bolt_port = 7688 if neo_7688 else (7687 if neo_7687 else None)
if bolt_port:
    uri = f"bolt://127.0.0.1:{bolt_port}"
    try:
        driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
        driver.verify_connectivity()
        print(f"Neo4j PING SUCCESS on {uri} with auth (neo4j/password)")
        driver.close()
    except Exception as e:
        try:
            driver = GraphDatabase.driver(uri, auth=("neo4j", "civix2026"))
            driver.verify_connectivity()
            print(f"Neo4j PING SUCCESS on {uri} with auth (neo4j/civix2026)")
            driver.close()
        except Exception as e2:
            print(f"Neo4j PING FAILED on {uri}: {e2}")
else:
    print("Neo4j is NOT listening on bolt port 7688 or 7687.")
