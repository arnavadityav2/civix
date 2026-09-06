import socket

ports = {
    "PostgreSQL 17 (Port 5432)": 5432,
    "PostgreSQL 16 (Port 5433)": 5433,
    "Neo4j Bolt (Port 7688)": 7688,
    "Neo4j Default Bolt (Port 7687)": 7687,
    "Neo4j HTTP (Port 7475)": 7475,
    "Neo4j Default HTTP (Port 7474)": 7474,
    "FastAPI Backend (Port 8000)": 8000,
    "Vite Frontend (Port 5173)": 5173
}

print("=== FAST PORT SOCKET SCAN ===")
for name, port in ports.items():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(("127.0.0.1", port))
        print(f"[ONLINE]  {name}")
    except Exception as e:
        print(f"[OFFLINE] {name} ({e})")
    finally:
        s.close()
