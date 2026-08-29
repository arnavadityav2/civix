import os
import csv
import json
import unittest
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import CivixGenerator
from config import OUTPUT_DIR

class TestPhase3D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Run generator
        cls.gen1 = CivixGenerator()
        cls.gen1.run()
        
        # Load generated data
        def load_json(name):
            with open(os.path.join(OUTPUT_DIR, name), "r", encoding="utf-8") as f:
                return json.load(f)
                
        def load_csv(name):
            with open(os.path.join(OUTPUT_DIR, name), "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
                
        cls.surv = load_json("surveillance_reports.json")
        cls.intel = load_json("intelligence_reports.json")
        cls.vs = load_csv("vehicle_sightings.csv")
        cls.hist = load_csv("criminal_history_records.csv")
        cls.prop = load_csv("property_transfers.csv")
            
        cls.lineage = load_json("lineage.json")

        cls.world = cls.gen1.canonical_world
        
        # Run a second time for reproducibility
        cls.gen2 = CivixGenerator()
        cls.gen2.run()
        
        cls.surv2 = load_json("surveillance_reports.json")
        cls.intel2 = load_json("intelligence_reports.json")
        cls.vs2 = load_csv("vehicle_sightings.csv")
        cls.hist2 = load_csv("criminal_history_records.csv")
        cls.prop2 = load_csv("property_transfers.csv")
        cls.lineage2 = load_json("lineage.json")

    def test_record_counts(self):
        self.assertEqual(len(self.surv), 12, "Exactly 12 surveillance reports")
        self.assertEqual(len(self.vs), 8, "Exactly 8 vehicle sightings")
        self.assertEqual(len(self.intel), 5, "Exactly 5 intelligence reports")
        self.assertEqual(len(self.hist), 6, "Exactly 6 criminal history records")
        self.assertEqual(len(self.prop), 3, "Exactly 3 property transfers")

    def test_reproducibility(self):
        self.assertEqual(self.surv, self.surv2, "Surveillance not perfectly reproducible")
        self.assertEqual(self.vs, self.vs2, "Vehicle sightings not perfectly reproducible")
        self.assertEqual(self.intel, self.intel2, "Intelligence not perfectly reproducible")
        self.assertEqual(self.hist, self.hist2, "History not perfectly reproducible")
        self.assertEqual(self.prop, self.prop2, "Property not perfectly reproducible")
        self.assertEqual(self.lineage, self.lineage2, "Lineage not perfectly reproducible")

    def test_references_exist(self):
        valid_persons = set(self.world.persons.keys())
        valid_locs = set(self.world.locations.keys())
        valid_vehicles = set([v.registration_number for v in self.world.vehicles.values()])
        valid_props = set(self.world.properties.keys())
        
        for s in self.surv:
            self.assertIn(s["location_id"], valid_locs)
            for e in s["entities_observed"]:
                self.assertIn(e, valid_persons)
                
        for v in self.vs:
            self.assertIn(v["location_id"], valid_locs)
            self.assertIn(v["registration"], valid_vehicles)
            if v["observed_person"]:
                self.assertIn(v["observed_person"], valid_persons)
                
        for i in self.intel:
            for e in i["entities_mentioned"]:
                self.assertIn(e, valid_persons)
                
        for h in self.hist:
            self.assertIn(h["person_id"], valid_persons)
            
        for p in self.prop:
            self.assertIn(p["property_id"], valid_props)
            self.assertIn(p["previous_owner_id"], valid_persons)
            self.assertIn(p["new_owner_id"], valid_persons)

    def test_date_range(self):
        start_date = datetime.fromisoformat("2026-06-01")
        end_date = datetime.fromisoformat("2026-08-31T23:59:59")
        
        for lst in [self.surv, self.vs, self.prop]:
            for r in lst:
                key = "timestamp" if "timestamp" in r else "date"
                dt = datetime.fromisoformat(r[key])
                self.assertTrue(start_date <= dt <= end_date, f"Date {dt} out of range")

    def test_forced_events_and_chains(self):
        # Surveillance: Cross-Network Meeting: Suresh and Harish meet at LOC-04 on Aug 12 at 13:00
        meet = [s for s in self.surv if s["location_id"] == "LOC-04" and "P-03" in s["entities_observed"] and "P-09" in s["entities_observed"]]
        self.assertGreaterEqual(len(meet), 1, "Missing cross-network meeting in surveillance")
        
        # Vehicle: Suresh's vehicle (RJ14CD5678) is sighted at Harish's residence (LOC-11) on Jul 15
        sight = [v for v in self.vs if v["registration"] == "RJ14CD5678" and v["location_id"] == "LOC-11" and v["timestamp"].startswith("2026-07-15")]
        self.assertGreaterEqual(len(sight), 1, "Missing critical vehicle sighting")
        
        # Property: Kamla Bai (P-14) -> Sunita Agarwal (P-12) etc.
        prop1 = [p for p in self.prop if p["property_id"] == "PROP-01" and p["previous_owner_id"] == "P-14" and p["new_owner_id"] == "P-12"]
        self.assertGreaterEqual(len(prop1), 1, "Missing PROP-01 transfer")

    def test_lineage_exists(self):
        lineage_ids = set([r["record_id"] for r in self.lineage])
        
        # Check that everything has a lineage ID and it maps
        for s in self.surv:
            self.assertIn(s["report_id"], lineage_ids)
            self.assertTrue(s["report_id"].startswith("SURV-"))
            
        for v in self.vs:
            self.assertIn(v["record_id"], lineage_ids)
            self.assertTrue(v["record_id"].startswith("VS-"))
            
        for i in self.intel:
            self.assertIn(i["report_id"], lineage_ids)
            self.assertTrue(i["report_id"].startswith("INTEL-"))
            
        for p in self.prop:
            self.assertIn(p["record_id"], lineage_ids)
            self.assertTrue(p["record_id"].startswith("PROP-TX-"))
            
        for h in self.hist:
            self.assertIn(h["record_id"], lineage_ids)
            self.assertTrue(h["record_id"].startswith("HIST-"))

    def test_no_ground_truth_in_raw(self):
        for lst in [self.surv, self.intel, self.vs, self.hist, self.prop]:
            for r in lst:
                r_str = json.dumps(r).lower()
                self.assertNotIn("forced", r_str)
                self.assertNotIn("ground_truth", r_str)
                self.assertNotIn("false lead", r_str)

if __name__ == "__main__":
    unittest.main()
