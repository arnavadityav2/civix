# Phase 5 Chunk 3: Cross-Universe Evaluation Summary

## 1. Experimental Context
The canonical prototype model (**Behavioral XGBoost**) was trained strictly on the V2A Original Training Split (175,000 entities, Temporal Cutoff = `2024-12-31`). It was evaluated entirely blind against the V2B and V2C unseen synthetic universes (50,000 entities each).

## 2. Cross-Universe Metrics Matrix

| Metric | V2A (Original Test Split) | V2B (Unseen Synthetic Universe) | V2C (Unseen Synthetic Universe) |
| :--- | :--- | :--- | :--- |
| **Total Entities** | 37,500 | 50,000 (Full) | 50,000 (Full) |
| **Positive Prevalence** | 10.19% | 10.17% | 10.06% |
| **ROC-AUC** | 0.8646 | 0.8492 [95% CI: 0.8431 - 0.8552] | 0.8523 [95% CI: 0.8463 - 0.8580] |
| **PR-AUC** | 0.5726 | 0.5531 [95% CI: 0.5385 - 0.5670] | 0.5551 [95% CI: 0.5413 - 0.5693] |
| **F1-Score** | 0.4824 | 0.4953 | 0.4994 |
| **Precision @ 1%** | 0.9360 | 0.9380 [95% CI: 0.9120 - 0.9600] | 0.9220 [95% CI: 0.8960 - 0.9460] |
| **Recall @ 1%** | 0.0918 | 0.0922 | 0.0916 |
| **Precision @ 5%** | 0.7323 | 0.7216 [95% CI: 0.7020 - 0.7412] | 0.7216 [95% CI: 0.7020 - 0.7416] |
| **Recall @ 5%** | 0.3592 | 0.3545 | 0.3586 |
| **Hard Negs in Top 1%** | 0 | 0 | 0 |

## 3. Analysis of Variance
* **Absolute Degradation:** PR-AUC degraded by roughly 0.0175 to 0.0195 points when moving from the V2A Test Split to the unseen evaluation universes.
* **Statistical Significance (Informal Check):** The V2A baseline PR-AUC (0.5726) point estimate falls outside the 95% Confidence Interval for V2B and just outside the 95% CI for V2C (margin of 0.0033). Because we do not have a CI for V2A itself, this is an informal check rather than a formal two-sample significance test, but it is suggestive of a real, if small, absolute degradation rather than mere sampling noise.
* **Operational Stability:** Despite the observed PR-AUC drop, the critical operational metric (Precision@1%) remained remarkably stable, with the V2A baseline sitting comfortably inside the 95% CIs of both V2B and V2C.

## 4. Final Prototype Decision
Based strictly on the executed evidence across three separate synthetic universes, the Behavioral XGBoost model is officially classified as:

**MODERATE CROSS-UNIVERSE GENERALIZATION**

**Reasoning:** The model successfully generalizes to parametric shifts within the V2 synthetic data framework, maintaining its critical P@1% operational performance. However, because all evaluation data is strictly synthetic-on-synthetic, and because the synthetic hard-negative construction was proven trivial (scoring lower than ordinary negatives), this test does not validate the model for real-world deployment or against real-world adversarial actors.
