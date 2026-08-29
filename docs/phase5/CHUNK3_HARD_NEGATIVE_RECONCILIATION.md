# Phase 5 Chunk 3: Hard Negative Reconciliation Report

## 1. Objective
This read-only audit reconciles a numeric discrepancy regarding the prevalence of "Hard Negatives" (entities where `is_false_positive = True`) in the V2A dataset. Earlier documentation estimated ~53,500 hard negatives (≈21.4%) in the full V2A population, whereas recent split-level audits found 25.02% prevalence. This report establishes the exact canonical ground-truth composition without modifying any data or rerunning inference.

## 2. Canonical Source
The canonical V2A ground truth was read from:
`D:\civix_data\synthetic\profile_v2_v2a\ground_truth\person_labels\*.parquet`

Authoritative split boundaries were read from:
`D:\civix_data\synthetic\profile_v2_v2a\ground_truth\train_val_test_split\*.parquet`

## 3. Exact Full V2A Count
* **Total Entities:** 250,000
* **Total `is_false_positive = 1`:** 63,285
* **Exact Full-Population Prevalence:** 25.31%

## 4. Exact Split-Level Counts
By joining the canonical labels against the canonical split artifact:
* **V2A TRAIN:** 175,000 entities | 44,300 hard negatives (25.31%)
* **V2A VALIDATION:** 37,500 entities | 9,575 hard negatives (25.53%)
* **V2A TEST:** 37,500 entities | 9,410 hard negatives (25.09%)

## 5. Split Construction Findings
The `train_val_test_split` artifact was structurally generated prior to ML pipeline execution. The parity of the prevalence across train/val/test (~25.3%) confirms that the split mechanism properly stratified the label distribution or utilized a sufficiently random draw to prevent compositional skew. 

## 6. Comparison with Old Estimate
An earlier approximate estimate of ~53,500 V2A hard negatives (≈21.4%) was not consistent with the canonical ground-truth recount. The exact read-only recount found 63,285 hard negatives out of 250,000 entities (25.31%). The earlier estimate is therefore superseded.

## 7. Cross-Universe Prevalence Table

| Universe / Split | Total Entities | Hard Negatives (`is_false_positive=1`) | Prevalence |
| :--- | :--- | :--- | :--- |
| **V2A (Full)** | 250,000 | 63,285 | 25.31% |
| V2A (Train) | 175,000 | 44,300 | 25.31% |
| V2A (Val) | 37,500 | 9,575 | 25.53% |
| V2A (Test) | 37,500 | 9,410 | 25.09% |
| **V2B (Full)** | 50,000 | 12,496 | 24.99% |
| **V2C (Full)** | 50,000 | 12,645 | 25.29% |

## 8. Statistical / Structural Interpretation
While extracting these counts, a deeper structural bug was discovered in the synthetic generator's output. The V2 generator config (`generation_config.json`) explicitly requested a `false_positive` scenario distribution of 5%. 
The generator *did* create exactly ~5% of entities with `scenario_class = 'false_positive'`. 

However, the binary `is_false_positive` flag (which the ML evaluation pipeline relies on) was incorrectly set to `1` for a massive subset of the `normal` scenario class. 
In V2A:
* True `false_positive` scenarios: 12,612
* `normal` scenarios incorrectly flagged as `is_false_positive=1`: 50,673
* **Total:** 63,285 (~25%)

This exact same bug perfectly replicated in V2B and V2C, causing the overall `is_false_positive` prevalence to hover precisely at ~25% across all three universes. The earlier ~5% narrative was referencing the *intended* config, while the canonical parquet files baked in a 25% prevalence due to this mapping bug.

## 9. Primary Label Integrity Check
Crucially, this flag-mapping bug is isolated strictly to the `is_false_positive` auxiliary flag. An explicit verification of the primary classification target (`is_positive_label`) confirms that it is perfectly clean. Out of the 250,000 V2A entities, exactly 24,920 have `is_positive_label = True`, and 100% of these entities belong to the `confirmed_pattern` scenario class. No `normal` or `false_positive` entities were accidentally swept into the primary target label. The 0.57 PR-AUC headline performance metric is methodologically sound and untouched by this bug.

## 10. Impact on Previous Phase 5 Conclusions
This finding changes the interpretation of the Hard Negative report. The earlier analysis was hopelessly diluted because ~80% of the "Hard Negatives" (50,673 / 63,285) were actually just `normal` scenario entities accidentally flagged as hard negatives. Because `normal` entities lack any suspicious behavior, they mechanically pulled the "hard negative" mean score down to the absolute bottom of the risk pool. The Hard Negative report must be re-run filtered explicitly to `scenario_class = 'false_positive'` to determine the model's true adversarial robustness.

## 11. Final Reconciliation Statement
**A. Earlier population estimate was incorrect; canonical prevalence is ~25%.**

The discrepancy is fully resolved. The 25% prevalence is stable across all splits and all universes, not because of structural robustness, but because a deterministic mapping bug in the generator conflated normal entities with false-positive entities in an identical manner every time it ran.
