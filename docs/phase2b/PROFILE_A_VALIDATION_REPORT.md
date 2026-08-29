# CIVIX Profile A Validation Report
**Profile**: development  
**Output**: C:\Users\ARNAV ADITYA\Desktop\civix 2.0\data\synthetic\profile_a  

| Test ID | Description | Status | Detail |
|---|---|---|---|
| T01 | Manifest file exists | OK PASS |  |
| T02 | Person count within 5% of target | OK PASS | expected~1000, got 1000 |
| T03_persons | Parquet readable: persons | OK PASS | 1,000 rows |
| T03_cdrs | Parquet readable: cdrs | OK PASS | 250,000 rows |
| T03_ground_truth/person_labels | Parquet readable: ground_truth/person_labels | OK PASS | 1,000 rows |
| T04 | CDR count within 5% of target | OK PASS | expected~250,000, got 250,000 |
| T05 | No duplicate person IDs | OK PASS | 0 duplicates |
| T06 | Scenario distribution within ±5pp | OK PASS | normal=0.70(exp 0.70) | suspicious=0.15(exp 0.15) | confirmed_pattern=0.11(exp 0.10) | false_positive=0.04(exp 0.05) |
| T07 | Ground truth columns absent from CDR features | OK PASS |  |
| T08 | CDR timestamps within date range | OK PASS | 2025-01-01 to 2025-06-30 |
| T09 | Hard negatives (false positives) present | OK PASS | 35 persons |
| T10 | TRAIN/VALIDATION/TEST splits all present | OK PASS | {'TEST': 150, 'VALIDATION': 150, 'TRAIN': 700} |
| T11 | No null caller_person_id in CDRs | OK PASS | 0 nulls |
| T12 | ≥10 distinct scenario families | OK PASS | 67 families found |
| T13 | Manifest has all required keys | OK PASS |  |
| T14 | Person[0] UUID matches deterministic seed | OK PASS | expected b3c88cf8-f36c-0d75-dc35-cb91636eaa99, got b3c88cf8-f36c-0d75-dc35-cb91636eaa99 |
| T15 | CDR duration distribution is non-uniform | OK PASS | std=106.8s, range=[20,599]s |
| T16 | Transaction amounts have long tail (Pareto-like) | OK PASS | avg=9833, max=500000, std=27671 |
| T17 | Cases generated | OK PASS | 100 cases |
| T18 | Checkpoint file exists | OK PASS |  |
| T19 | Multiple cell sectors used in CDRs | OK PASS | 150 distinct sectors |
| T20 | ≥5 stages completed (no premature OOM halt) | OK PASS | 13 stages completed |

**Total**: 22 PASS / 0 FAIL
