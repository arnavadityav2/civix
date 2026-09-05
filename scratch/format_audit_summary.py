import json

def analyze():
    with open(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\scratch\audit_raw_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=== 1. MANIFEST VERIFICATION ===")
    for m in data["manifest_verification"]:
        print(f"[{'PASS' if m['match'] else 'FAIL'}] {m['manifest_number']} | {m['manifest_title']} | DB Station: {m['db_police_station']}")

    print("\n=== 2. BASELINE POSTGRES INVENTORY (13 CASES) ===")
    print(f"{'Case Number':<14} | {'Roles':<5} | {'Ent':<4} | {'P':<3} | {'V':<3} | {'Ph':<3} | {'D':<3} | {'Evt':<4} | {'EvtP':<4} | {'Ass':<4} | {'Ld':<3} | {'FIR':<3} | {'Evid':<4}")
    print("-" * 80)
    for b in data["case_baselines"]:
        print(f"{b['case_number']:<14} | {b['roles_count']:<5} | {b['unique_entities']:<4} | {b['persons']:<3} | {b['vehicles']:<3} | {b['phones']:<3} | {b['devices']:<3} | {b['events_count']:<4} | {b['unique_event_participants']:<4} | {b['assertions_count']:<4} | {b['leads_count']:<3} | {b['firs_count']:<3} | {b['evidence_artifacts']:<4}")

    print("\n=== 3. NEO4J HOP EXPANSION PER CASE ===")
    print(f"{'Case Number':<14} | {'0-Hop':<5} | {'1-Hop':<5} | {'2-Hop':<5} | {'3-Hop':<5} | {'4-Hop':<5} | {'5-Hop':<5}")
    print("-" * 65)
    for n in data["neo4j_inventories"]:
        h = n["hops"]
        h0 = h.get("0_hop", {}).get("total_nodes", 0)
        h1 = h.get("1_hop", {}).get("total_nodes", 0)
        h2 = h.get("2_hop", {}).get("total_nodes", 0)
        h3 = h.get("3_hop", {}).get("total_nodes", 0)
        h4 = h.get("4_hop", {}).get("total_nodes", 0)
        h5 = h.get("5_hop", {}).get("total_nodes", 0)
        print(f"{n['case_number']:<14} | {h0:<5} | {h1:<5} | {h2:<5} | {h3:<5} | {h4:<5} | {h5:<5}")

    print("\n=== 4. NEO4J LABELS IN GOLDEN CASES ===")
    for lbl, info in data["neo4j_global_labels"].items():
        print(f"Label: {lbl:<20} | Global: {info['global_count']:<6} | Golden Nodes: {info['golden_node_count']:<6} | Golden Cases: {info['golden_cases_count']:<3}")

    print("\n=== 5. API VS NEO4J PARITY ===")
    print(f"{'Case Number':<14} | {'API Depth 1 Nodes':<18} | {'API Depth 2 Nodes':<18} | {'Neo4j 1-Hop':<12} | {'Neo4j 2-Hop':<12} | {'Neo4j 5-Hop':<12}")
    print("-" * 85)
    for a in data["api_parity"]:
        cnum = a["case_number"]
        n_info = next((n for n in data["neo4j_inventories"] if n["case_number"] == cnum), None)
        h1 = n_info["hops"]["1_hop"]["total_nodes"] if n_info else 0
        h2 = n_info["hops"]["2_hop"]["total_nodes"] if n_info else 0
        h5 = n_info["hops"]["5_hop"]["total_nodes"] if n_info else 0
        print(f"{cnum:<14} | {a['api_depth_1_nodes']:<18} | {a['api_depth_2_nodes']:<18} | {h1:<12} | {h2:<12} | {h5:<12}")

if __name__ == "__main__":
    analyze()
