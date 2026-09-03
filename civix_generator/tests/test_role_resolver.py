import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from civix_generator.large.scenarios import RoleResolver

def test_determinism():
    class MockConfig:
        def __init__(self):
            self.persons = 15000
            self.seed = 42
    
    config = MockConfig()
    
    # 1. Manifest V1
    manifest_v1 = {
        "investigations": {
            "cases": [
                {
                    "case_id": "DELHI-2026-HL-001",
                    "roles": [
                        {"role_id": "HL001_PRIMARY_01"},
                        {"role_id": "HL001_SECONDARY_02"}
                    ]
                }
            ]
        }
    }
    
    resolver_v1 = RoleResolver(config)
    idx_1 = resolver_v1.resolve("DELHI-2026-HL-001", "HL001_PRIMARY_01")
    idx_2 = resolver_v1.resolve("DELHI-2026-HL-001", "HL001_SECONDARY_02")
    
    # 2. Manifest V2 (add unrelated scenario)
    manifest_v2 = {
        "investigations": {
            "cases": [
                {
                    "case_id": "DELHI-2026-UNRELATED-999",
                    "roles": [
                        {"role_id": "UNRELATED_01"}
                    ]
                },
                {
                    "case_id": "DELHI-2026-HL-001",
                    "roles": [
                        {"role_id": "HL001_PRIMARY_01"},
                        {"role_id": "HL001_SECONDARY_02"}
                    ]
                }
            ]
        }
    }
    
    resolver_v2 = RoleResolver(config)
    idx_unrelated = resolver_v2.resolve("DELHI-2026-UNRELATED-999", "UNRELATED_01")
    idx_1_v2 = resolver_v2.resolve("DELHI-2026-HL-001", "HL001_PRIMARY_01")
    idx_2_v2 = resolver_v2.resolve("DELHI-2026-HL-001", "HL001_SECONDARY_02")
    
    assert idx_1 == idx_1_v2, f"Determinism failed: {idx_1} != {idx_1_v2}"
    assert idx_2 == idx_2_v2, f"Determinism failed: {idx_2} != {idx_2_v2}"
    
    print("RoleResolver Determinism Test: PASSED")

if __name__ == "__main__":
    test_determinism()
