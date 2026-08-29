# Phase 5 Chunk 3: Final Generalization Report

## Overview
This report details the retrospective final-outcome evaluation of the canonical `behavioral_xgboost_20260829T202007` model (trained solely on V2A) applied to the V2B and V2C synthetic universes.

## Baseline V2A (Historical Reference - Original Test Split)
* **Prevalence:** ~10.19%
* **ROC-AUC:** 0.8646
* **PR-AUC:** 0.5726

---

## V2B Unseen Synthetic Evaluation
* **Total Entities:** 50,000
* **Positive Entities:** 5,089
* **Prevalence:** 10.17%

**Metrics:**
* **ROC-AUC:** 0.8492 [95% CI: 0.8431 - 0.8552]
* **PR-AUC:** 0.5531 [95% CI: 0.5385 - 0.5670]
* **F1-Score:** 0.4953 (Threshold 0.5 - Note: 0.5 is not the operational alerting threshold)
* **Precision:** 0.4054
* **Recall:** 0.6367

**Investigative Alert Budgets:**
* **Precision @ 1%:** 0.9380 [95% CI: 0.9120 - 0.9600]
* **Recall @ 1%:** 0.0922
* **Precision @ 5%:** 0.7216 [95% CI: 0.7020 - 0.7412]
* **Recall @ 5%:** 0.3545

**Confusion Matrix (at 0.5 Threshold):**
```text
[[40158, 4753],
 [ 1849, 3240]]
```

---

## V2C Unseen Synthetic Evaluation
* **Total Entities:** 50,000
* **Positive Entities:** 5,031
* **Prevalence:** 10.06%

**Metrics:**
* **ROC-AUC:** 0.8523 [95% CI: 0.8463 - 0.8580]
* **PR-AUC:** 0.5551 [95% CI: 0.5413 - 0.5693]
* **F1-Score:** 0.4994 (Threshold 0.5)
* **Precision:** 0.4087
* **Recall:** 0.6418

**Investigative Alert Budgets:**
* **Precision @ 1%:** 0.9220 [95% CI: 0.8960 - 0.9460]
* **Recall @ 1%:** 0.0916
* **Precision @ 5%:** 0.7216 [95% CI: 0.7020 - 0.7416]
* **Recall @ 5%:** 0.3586

**Confusion Matrix (at 0.5 Threshold):**
```text
[[40298, 4671],
 [ 1802, 3229]]
```

---

## Conclusion
The V2A-trained Behavioral XGBoost model demonstrates strong cross-universe generalization within the V2 synthetic data-generating framework. Performance remains broadly stable across V2B and V2C despite measurable parametric distribution shifts. 

**Limitations:**
1. These are retrospective final-outcome evaluations and must not be presented as real-time early-warning or deployment-ready performance.
2. This does not establish real-world deployment validity or robustness to real-world adversarial behavior.
