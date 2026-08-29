import os
import csv
import json
import unittest
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import CivixGenerator
from config import OUTPUT_DIR

class TestPhase3C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Run generator
        cls.gen1 = CivixGenerator()
        cls.gen1.run()
        
        # Load generated data
        cls.cdrs = []
        with open(os.path.join(OUTPUT_DIR, "cdrs.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cls.cdrs = list(reader)
            
        cls.txs = []
        with open(os.path.join(OUTPUT_DIR, "transactions.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cls.txs = list(reader)
            
        with open(os.path.join(OUTPUT_DIR, "lineage.json"), "r", encoding="utf-8") as f:
            cls.lineage = json.load(f)

        cls.world = cls.gen1.canonical_world
        
        # Run a second time for reproducibility
        cls.gen2 = CivixGenerator()
        cls.gen2.run()
        
        cls.cdrs2 = []
        with open(os.path.join(OUTPUT_DIR, "cdrs.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cls.cdrs2 = list(reader)
            
        cls.txs2 = []
        with open(os.path.join(OUTPUT_DIR, "transactions.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cls.txs2 = list(reader)

    def test_record_counts(self):
        self.assertEqual(len(self.cdrs), 385, "Exactly 385 CDRs should be generated")
        self.assertEqual(len(self.txs), 50, "Exactly 50 financial transactions should be generated")

    def test_reproducibility(self):
        self.assertEqual(self.cdrs, self.cdrs2, "CDRs are not perfectly reproducible")
        self.assertEqual(self.txs, self.txs2, "Transactions are not perfectly reproducible")

    def test_references_exist_cdrs(self):
        valid_phones = set(self.world.phones.keys())
        for cdr in self.cdrs:
            self.assertIn(cdr["caller_msisdn"], valid_phones, f"Unknown caller phone {cdr['caller_msisdn']}")
            self.assertIn(cdr["receiver_msisdn"], valid_phones, f"Unknown receiver phone {cdr['receiver_msisdn']}")

    def test_references_exist_txs(self):
        valid_accounts = set([acc.account_number_masked for acc in self.world.accounts.values()])
        for tx in self.txs:
            self.assertIn(tx["sender_account"], valid_accounts, f"Unknown sender account {tx['sender_account']}")
            self.assertIn(tx["receiver_account"], valid_accounts, f"Unknown receiver account {tx['receiver_account']}")

    def test_date_range(self):
        start_date = datetime.fromisoformat("2026-06-01")
        end_date = datetime.fromisoformat("2026-08-31T23:59:59")
        
        for cdr in self.cdrs:
            dt = datetime.fromisoformat(cdr["timestamp"])
            self.assertTrue(start_date <= dt <= end_date, f"CDR Date {dt} out of range")
            
        for tx in self.txs:
            dt = datetime.fromisoformat(tx["timestamp"])
            self.assertTrue(start_date <= dt <= end_date, f"TX Date {dt} out of range")

    def test_forced_events(self):
        # 1. Alpha Comm Spike: Aug 13, Vikram and Amit must communicate exactly 12 times
        aug_13_calls = [
            c for c in self.cdrs 
            if c["timestamp"].startswith("2026-08-13") 
            and ((c["caller_msisdn"] == "9876543210" and c["receiver_msisdn"] == "9123456789") or 
                 (c["caller_msisdn"] == "9123456789" and c["receiver_msisdn"] == "9876543210"))
        ]
        self.assertGreaterEqual(len(aug_13_calls), 12, "Missing Alpha Comm Spike (12 calls on Aug 13)")

        # 2. Alpha Financial Spike: Aug 10, Vikram transfers exactly 1,50,000 to Amit
        spike_tx = [
            t for t in self.txs 
            if t["timestamp"].startswith("2026-08-10") 
            and float(t["amount"]) == 150000.0
            and t["sender_account"] == "HDFC-****4523" # Vikram
            and t["receiver_account"] == "HDFC-****6234" # Amit
        ]
        self.assertEqual(len(spike_tx), 1, "Missing Alpha Financial Spike (1.5L on Aug 10)")
        
        # 3. Cross-Network Finance: Jun 22 (2L), Jul 22 (1.5L), Aug 16 (3L)
        joint = "PNB-****8877"
        tx_j1 = [t for t in self.txs if t["timestamp"].startswith("2026-06-22") and t["receiver_account"] == joint and float(t["amount"]) == 200000.0]
        tx_j2 = [t for t in self.txs if t["timestamp"].startswith("2026-07-22") and t["receiver_account"] == joint and float(t["amount"]) == 150000.0]
        tx_j3 = [t for t in self.txs if t["timestamp"].startswith("2026-08-16") and t["receiver_account"] == joint and float(t["amount"]) == 300000.0]
        
        self.assertEqual(len(tx_j1), 1, "Missing Jun 22 Joint Account transfer")
        self.assertEqual(len(tx_j2), 1, "Missing Jul 22 Joint Account transfer")
        self.assertEqual(len(tx_j3), 1, "Missing Aug 16 Joint Account transfer")

    def test_lineage_exists(self):
        lineage_ids = set([r["record_id"] for r in self.lineage])
        for cdr in self.cdrs:
            self.assertIn(cdr["record_id"], lineage_ids, f"Missing lineage for CDR {cdr['record_id']}")
            self.assertTrue(cdr["record_id"].startswith("CDR-"), "Sequential ID should be used")
            
        for tx in self.txs:
            self.assertIn(tx["record_id"], lineage_ids, f"Missing lineage for TX {tx['record_id']}")
            self.assertTrue(tx["record_id"].startswith("TX-"), "Sequential ID should be used")

    def test_no_ground_truth_in_raw(self):
        # We shouldn't see 'ground_truth_relevance' or 'is_forced_event' or 'rule' in the output CSVs
        for cdr in self.cdrs:
            self.assertNotIn("is_forced", json.dumps(cdr).lower())
            self.assertNotIn("anomaly", json.dumps(cdr).lower())
            
        for tx in self.txs:
            self.assertNotIn("forced", json.dumps(tx).lower())
            self.assertNotIn("ground_truth", json.dumps(tx).lower())

if __name__ == "__main__":
    unittest.main()
