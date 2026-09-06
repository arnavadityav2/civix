import socket
import time
from neo4j import GraphDatabase

print("Waiting for Neo4j to listen on ports...")
neo_online = False

for i in range(15):
    for port in [7688, 7687]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex(("127.0.0.1", port))
        s.close()
        if res == 0:
            print(f"Neo4j Bolt port {port} is OPEN!")
            neo_online = True
            active_port = port
            break
    if neo_online:
        break
    time.sleep(2)

if neo_online:
    uri = f"bolt://127.0.0.1:{active_port}"
    for auth in [("neo4j", "password"), ("neo4j", "civix2026")]:
        try:
            driver = GraphDatabase.driver(uri, auth=auth)
            driver.verify_connectivity()
            print(f"Neo4j PING SUCCESSFUL on {uri} with auth {auth[0]}/{auth[1]}!")
            driver.close()
            break
        except Exception as e:
            print(f"Auth test {auth}: {e}")
else:
    print("Neo4j did not open bolt ports within 30 seconds.")
