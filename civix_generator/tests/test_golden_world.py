import os
import sys

# Ensure imports work from generator directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.golden_world import GoldenWorldValidator
from config import OUTPUT_DIR

def run_golden_validation():
    validator = GoldenWorldValidator(OUTPUT_DIR)
    
    # 1. H1 - H4
    h1 = "PASS" if validator.validate_h1() else "FAIL"
    h2 = "PASS" if validator.validate_h2() else "FAIL"
    h3 = "PASS" if validator.validate_h3() else "FAIL"
    h4 = "PASS" if validator.validate_h4() else "FAIL"
    
    # 2. Anomalies
    anomalies = {}
    for i in range(1, 9):
        sig = f"SIG-{i:02d}"
        anomalies[sig] = "PASS" if validator.validate_anomaly(sig) else "FAIL"
        
    # 3. False Leads
    false_leads = {}
    for i in range(1, 7):
        fl = f"FL-{i:02d}"
        false_leads[fl] = "PASS" if validator.validate_false_leads(fl) else "FAIL"
        
    # 4. Entity Resolution
    er_pass = validator.validate_entity_resolution()
    
    # 5. Provenance
    prov_pass = validator.validate_provenance()
    
    # 6. Epistemic
    epi_pass = validator.validate_epistemic()
    
    # 7. Print Report
    print("CIVIX GOLDEN WORLD VALIDATION")
    print("==============================")
    print("")
    print("Hidden relationships")
    print(f"H1: {h1}")
    print(f"H2: {h2}")
    print(f"H3: {h3}")
    print(f"H4: {h4}")
    print("")
    print("Anomaly evidence")
    for sig, res in anomalies.items():
        print(f"{sig}: {res}")
    print("")
    print("False leads")
    for fl, res in false_leads.items():
        print(f"{fl}: {res}")
    print("")
    print("Entity-resolution challenges")
    print("12/12 evidence sets present" if er_pass else "Missing ER evidence sets")
    print("4/4 DO-NOT-MERGE safeguards present" if er_pass else "Missing DO-NOT-MERGE safeguards")
    print("")
    print("Provenance")
    print("100% records mapped to lineage" if prov_pass else "Lineage gaps detected")
    print("")
    print("Epistemic separation")
    print("PASS" if epi_pass else "FAIL - Ground truth leakage detected")
    print("")
    print("==============================")
    all_pass = all([
        h1 == "PASS", h2 == "PASS", h3 == "PASS", h4 == "PASS",
        all(v == "PASS" for v in anomalies.values()),
        all(v == "PASS" for v in false_leads.values()),
        er_pass, prov_pass, epi_pass
    ])
    print(f"GOLDEN WORLD VALIDATION: {'PASS' if all_pass else 'FAIL (Inconsistencies Discovered)'}")

if __name__ == "__main__":
    run_golden_validation()
