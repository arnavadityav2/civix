import json
import psycopg2

def map_manifests():
    with open("demo_world/manifests/investigations.json", "r") as f:
        inv_manifest = json.load(f)

    with open("demo_world/manifests/evidence.json", "r") as f:
        ev_manifest = json.load(f)

    print("==========================================================")
    print("MANIFEST MAPPING AUDIT")
    print("==========================================================")
    print(f"Investigations in manifest: {len(inv_manifest)}")
    
    # Check 12 Hero cases in manifest
    hero_cases = inv_manifest[:12] if isinstance(inv_manifest, list) else inv_manifest.get("cases", [])[:12]
    print(f"Hero cases sample from manifest:")
    for h in hero_cases[:5]:
        print(f"  - {h}")

    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM civix.investigative_case;")
    db_case_count = cur.fetchone()[0]
    print(f"\nTotal cases in civix_demo database: {db_case_count}")

    conn.close()

if __name__ == "__main__":
    map_manifests()
