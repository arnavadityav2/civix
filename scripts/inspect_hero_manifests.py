import json

def inspect_hero_manifests():
    with open("demo_world/manifests/investigations.json", "r") as f:
        inv_data = json.load(f)["investigations"]

    print("==========================================================")
    print("HERO CASES IN MANIFEST:")
    print("==========================================================")
    for idx, c in enumerate(inv_data):
        cnum = c.get("case_number", c.get("id", f"HL-00{idx+1}"))
        title = c.get("title", c.get("name", "Untitled"))
        cid = c.get("case_id", "N/A")
        print(f"Case {idx+1}: {cnum} | ID: {cid} | Title: {title}")

    with open("demo_world/manifests/evidence.json", "r") as f:
        ev_data = json.load(f)["evidence"]

    print("\n==========================================================")
    print("EVIDENCE KEYS IN MANIFEST:")
    print("==========================================================")
    for k in list(ev_data.keys())[:10]:
        print(f"  - Key: {k}")

if __name__ == "__main__":
    inspect_hero_manifests()
