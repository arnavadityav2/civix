import json
import os
from typing import Dict, Any

class ManifestValidator:
    def __init__(self):
        pass
        
    def validate_world(self, data: Dict[str, Any]):
        assert "population_size" in data, "Missing population_size"
        assert "geography" in data, "Missing geography"
        
    def validate_investigations(self, data: Dict[str, Any]):
        assert "cases" in data, "Missing cases"
        for case in data["cases"]:
            assert "case_id" in case
            assert "roles" in case
            assert "title" in case
            
    def validate_ground_truth(self, data: Dict[str, Any]):
        assert "relationships" in data, "Missing relationships"
        for rel in data["relationships"]:
            assert "role_a" in rel
            assert "role_b" in rel
            assert "is_positive" in rel
            
    def validate_evidence(self, data: Dict[str, Any]):
        assert "constraints" in data, "Missing constraints"
        for c in data["constraints"]:
            assert "event_type" in c
            assert "actor" in c

def load_and_validate_manifests(manifest_dir: str) -> Dict[str, Any]:
    validator = ManifestValidator()
    
    world_path = os.path.join(manifest_dir, "world.json")
    with open(world_path, "r") as f:
        world = json.load(f)
    validator.validate_world(world)
    
    investigations_path = os.path.join(manifest_dir, "investigations.json")
    with open(investigations_path, "r") as f:
        investigations = json.load(f)
    validator.validate_investigations(investigations)
    
    gt_path = os.path.join(manifest_dir, "ground_truth.json")
    with open(gt_path, "r") as f:
        ground_truth = json.load(f)
    validator.validate_ground_truth(ground_truth)
    
    evidence_path = os.path.join(manifest_dir, "evidence.json")
    with open(evidence_path, "r") as f:
        evidence = json.load(f)
    validator.validate_evidence(evidence)
    
    return {
        "world": world,
        "investigations": investigations,
        "ground_truth": ground_truth,
        "evidence": evidence
    }
