import os
import shutil
import subprocess
import time
import socket

def provision_demo_neo4j():
    print("==========================================================")
    print("PROVISIONING ISOLATED DEMO NEO4J INSTANCE (PORT 7688)")
    print("==========================================================")
    
    src_dir = os.path.abspath("scratch/neo4j/neo4j-community-5.23.0")
    demo_dir = os.path.abspath("scratch/neo4j_demo/neo4j-community-5.23.0")
    
    if not os.path.exists(demo_dir):
        print(f"Copying Neo4j install to {demo_dir}...")
        shutil.copytree(src_dir, demo_dir)
        print("[PASS] Neo4j instance directory copied.")
        
        # Clear data directory for clean instance
        data_dir = os.path.join(demo_dir, "data")
        logs_dir = os.path.join(demo_dir, "logs")
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
            os.makedirs(data_dir, exist_ok=True)
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir)
            os.makedirs(logs_dir, exist_ok=True)
        print("[PASS] Fresh data directory initialized.")
        
    # Configure ports in conf/neo4j.conf
    conf_path = os.path.join(demo_dir, "conf", "neo4j.conf")
    with open(conf_path, "r", encoding="utf-8") as f:
        conf_lines = f.readlines()
        
    new_lines = []
    for line in conf_lines:
        if line.strip().startswith("#server.bolt.listen_address=:7687") or line.strip().startswith("server.bolt.listen_address="):
            new_lines.append("server.bolt.listen_address=:7688\n")
        elif line.strip().startswith("#server.http.listen_address=:7474") or line.strip().startswith("server.http.listen_address="):
            new_lines.append("server.http.listen_address=:7475\n")
        else:
            new_lines.append(line)
            
    with open(conf_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("[PASS] neo4j.conf configured with Bolt port 7688 & HTTP port 7475.")

    # Check if port 7688 is already running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    res = s.connect_ex(("localhost", 7688))
    s.close()
    
    if res == 0:
        print("[PASS] Isolated Demo Neo4j instance is already running on port 7688.")
        return True
        
    print("Launching Demo Neo4j Community Server process on port 7688...")
    cmd = ["powershell", "-Command", f"Start-Process -FilePath '{os.path.join(demo_dir, 'bin', 'neo4j.bat')}' -ArgumentList 'console'"]
    subprocess.run(cmd, check=True)
    
    # Wait for port 7688 to become open
    print("Waiting for Neo4j Demo instance on port 7688 to boot...")
    for _ in range(15):
        time.sleep(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        r = s.connect_ex(("localhost", 7688))
        s.close()
        if r == 0:
            print("[PASS] ISOLATED DEMO NEO4J INSTANCE IS ONLINE ON PORT 7688.")
            return True
            
    print("[FAIL] Timeout waiting for Demo Neo4j on port 7688.")
    return False

if __name__ == "__main__":
    provision_demo_neo4j()
