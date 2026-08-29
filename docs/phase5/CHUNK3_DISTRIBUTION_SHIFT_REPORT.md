# Phase 5 Chunk 3: Distribution Shift Report

## Overview
This report analyzes parametric distribution shifts within the V2 synthetic data-generating framework across the V2A training universe and the V2B/V2C evaluation universes.

## Baseline (V2A) vs V2B Shift
The V2B universe exhibited significant structural shifts compared to V2A. 
* **Most Shifted Feature:** `unique_cell_sectors` (and `unique_sectors`), which dropped by **30.95%** (V2A Mean: 214.89, V2B Mean: 148.37).
* **Communication Volume:** Overall call activity was heavily suppressed in V2B. `total_calls` dropped by 20.14%, `voice_calls` by 20.15%, and `night_call_count` by 20.19%.
* **Financial Volume:** The total money moved (`total_sent_amount`) dropped by 17.15%, while the frequency of `high_value_txn_count` dropped by 16.67%.

## Baseline (V2A) vs V2C Shift
The V2C universe exhibited nearly identical distribution shifts to V2B.
* **Most Shifted Feature:** `unique_cell_sectors` dropped by **30.92%** (Mean: 148.45).
* **Communication Volume:** `total_calls` dropped by 20.01%, `voice_calls` by 20.02%, and `night_call_count` by 20.06%.
* **Financial Volume:** `total_sent_amount` dropped by 16.44%, while `high_value_txn_count` dropped by 16.67%.

## Conclusion
The data distributions in V2B and V2C are not identical to V2A. There is substantial, measurable downward distribution shift across spatial, behavioral, and financial feature domains. 

> [!WARNING]
> **Interpretation Limit:** These shifts represent changes to the scale parameters within the synthetic generator itself. Robustness to these shifts demonstrates that the model is somewhat insensitive to these specific volume reductions, but this **does not** establish real-world distribution shift survival.
