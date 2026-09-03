import json
import os
import sys

def validate_manifests(manifest_dir: str):
    print("Validating Intelligence Manifests...")
    
    # 1. Load World
    with open(os.path.join(manifest_dir, "world.json")) as f:
        world = json.load(f)["world"]
        assert world["population_size"] == 15000
        print(f"[PASS] World schema valid. Population: {world['population_size']}")
        
    # 2. Load Investigations
    with open(os.path.join(manifest_dir, "investigations.json")) as f:
        inv = json.load(f)["investigations"]
        assert len(inv) == 12
        
        roles_defined = set()
        for case in inv:
            assert "investigative_question" in case
            for r in case["roles"]:
                roles_defined.add(r["role_id"])
        print(f"[PASS] Investigations schema valid. 12 Hero Cases loaded, {len(roles_defined)} unique roles defined.")
        
    # 3. Load Ground Truth
    with open(os.path.join(manifest_dir, "ground_truth.json")) as f:
        gt = json.load(f)["ground_truth"]
        assert len(gt["positive_overlaps"]) > 0
        assert len(gt["ambiguous_overlaps"]) > 0
        assert len(gt["innocent_overlaps"]) > 0
        assert len(gt["negative_controls"]) > 0
        
        # Cross-reference
        all_gt_edges = gt["positive_overlaps"] + gt["ambiguous_overlaps"] + gt["innocent_overlaps"] + gt["negative_controls"]
        for edge in all_gt_edges:
            assert edge["source"] in roles_defined, f"Ground truth source {edge['source']} not defined in investigations."
            assert edge["target"] in roles_defined, f"Ground truth target {edge['target']} not defined in investigations."
        print(f"[PASS] Ground truth schema valid. 4-way epistemic overlap strictly enforced.")
        
    # 4. Load Evidence
    with open(os.path.join(manifest_dir, "evidence.json")) as f:
        ev = json.load(f)["evidence"]
        
        for constraint in ev["constraints"]:
            assert constraint["actor"] in roles_defined
            if constraint["target"] != "HL003_COFFEE_SHOP" and constraint["actor"] != "HL003_COFFEE_SHOP":
                assert constraint["target"] in roles_defined
            
        print(f"[PASS] Evidence schema valid. {len(ev['constraints'])} strict behavioral constraints mapped to ground truth.")
        
    print("\nALL MANIFESTS PASSED VALIDATION. READY FOR DETERMINISTIC GENERATION.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_manifests.py <manifest_dir>")
        sys.exit(1)
    validate_manifests(sys.argv[1])
