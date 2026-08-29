import unittest
import os
import sys
import copy
from typing import Any

# Ensure imports work from generator directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.golden_world import GoldenWorldValidator
from config import OUTPUT_DIR

class TestPhase4BNegative(unittest.TestCase):
    def setUp(self):
        self.validator = GoldenWorldValidator(OUTPUT_DIR)
        # Deep copy original records to manipulate them safely
        self.original_txs = copy.deepcopy(self.validator.txs)
        self.original_vs = copy.deepcopy(self.validator.vs)
        self.original_cdrs = copy.deepcopy(self.validator.cdrs)

    def test_sig03_negative(self):
        # Assert initially passes
        self.assertTrue(self.validator.validate_anomaly("SIG-03"))
        
        # Remove LOC-04 sighting for Suresh
        self.validator.vs = [v for v in self.validator.vs if not (v["registration"] == "RJ14CD5678" and v["location_id"] == "LOC-04")]
        
        # Should now fail
        self.assertFalse(self.validator.validate_anomaly("SIG-03"))
        
    def test_sig05_negative(self):
        # Assert initially passes
        self.assertTrue(self.validator.validate_anomaly("SIG-05"))
        
        # Alter Dinesh's tx amount so it no longer totals 3.25L
        for t in self.validator.txs:
            if float(t["amount"]) == 125000.0:
                t["amount"] = "50000.0"
                break
                
        # Should now fail
        self.assertFalse(self.validator.validate_anomaly("SIG-05"))

    def test_sig06_negative(self):
        # Assert initially passes
        self.assertTrue(self.validator.validate_anomaly("SIG-06"))
        
        # Remove one 75K tx
        for i, t in enumerate(self.validator.txs):
            if float(t["amount"]) == 75000.0:
                self.validator.txs.pop(i)
                break
                
        # Should now fail
        self.assertFalse(self.validator.validate_anomaly("SIG-06"))

    def test_sig08_negative(self):
        # Assert initially passes
        self.assertTrue(self.validator.validate_anomaly("SIG-08"))
        
        # Remove one periodic call between Bhupendra and Gopal
        # Just remove the first call that matches the numbers
        for i, c in enumerate(self.validator.cdrs):
            nums = {c["caller_msisdn"], c["receiver_msisdn"]}
            if "9777888999" in nums and "9000777888" in nums:
                self.validator.cdrs.pop(i)
                break
                
        # Should now fail
        self.assertFalse(self.validator.validate_anomaly("SIG-08"))

if __name__ == '__main__':
    unittest.main()
