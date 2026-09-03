import json

def inspect_manifest_keys():
    with open("demo_world/manifests/investigations.json", "r") as f:
        inv = json.load(f)
    print("investigations.json keys:", list(inv.keys()) if isinstance(inv, dict) else f"List of length {len(inv)}")
    if isinstance(inv, dict):
        for k, v in inv.items():
            print(f"  Key '{k}': type {type(v)}, count {len(v) if isinstance(v, (list, dict)) else 'N/A'}")

    with open("demo_world/manifests/evidence.json", "r") as f:
        ev = json.load(f)
    print("\nevidence.json keys:", list(ev.keys()) if isinstance(ev, dict) else f"List of length {len(ev)}")
    if isinstance(ev, dict):
        for k, v in ev.items():
            print(f"  Key '{k}': type {type(v)}, count {len(v) if isinstance(v, (list, dict)) else 'N/A'}")

if __name__ == "__main__":
    inspect_manifest_keys()
