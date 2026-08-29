# Phase 5 Chunk 3: Post-Evaluation Audit

## 1. V2A Baseline Reconciliation
* **Finding:** The original V2A test predictions (raw probabilities for the 37,500 test entities) were computed in-memory during Phase 2 and discarded after logging the metrics to `behavioral_xgboost_20260829T202007.json`.
* **Action Taken:** Because the canonical model rules explicitly forbid re-running inference to regenerate missing artifacts, it was scientifically impossible to compute bootstrap confidence intervals or raw score distributions for the V2A baseline. 
* **Correction:** The Cross-Universe report was updated to explicitly demarcate V2A as the "Original Test Split" (N=37,500), preventing it from being confused with the 175,000 training population.

## 2. Hard-Negative Score-Distribution Analysis
* **Finding:** The previous claim that the model was "invulnerable" because 0 hard negatives entered the Top 1% alert budget was methodologically flawed.
* **Action Taken:** A raw score audit on V2B and V2C was executed. The distribution revealed:
  * V2B True Positives Mean: 0.6385
  * V2B Ordinary Negatives Mean: 0.2683
  * V2B **Hard Negatives Mean: 0.2079**
* **Correction:** The designated synthetic `false_positive` entities received lower risk scores than randomly selected ordinary negatives. The highest ranked hard negative out of 50,000 entities was 821st. The model did not perform sophisticated adversarial filtering; the synthetic generator simply generated trivial hard negatives. The reports were updated to remove the word "invulnerable".

## 3. Bootstrap Methodology & Confidence Intervals
* **Methodology:** 1,000 bootstrap replicates (Seed = 42) were drawn with replacement from the full 50,000-entity population for V2B and V2C.
* **V2B 95% CIs:**
  * ROC-AUC: 0.8431 - 0.8552
  * PR-AUC: 0.5385 - 0.5670
  * P@1%: 0.9120 - 0.9600
  * P@5%: 0.7020 - 0.7412
* **V2C 95% CIs:**
  * ROC-AUC: 0.8463 - 0.8580
  * PR-AUC: 0.5413 - 0.5693
  * P@1%: 0.8960 - 0.9460
  * P@5%: 0.7020 - 0.7416
* **Correction:** The V2A baseline PR-AUC (0.5726) point estimate sits *outside* the V2B CI and just outside the V2C CI (margin of 0.0033). Because we do not have a CI for V2A itself, this is an informal check rather than a formal two-sample significance test, but it is suggestive of a real, albeit operationally small, absolute degradation rather than mere sampling noise.

## 4. Distribution Shift Re-interpretation
* **Finding:** Previous reports implied survival against "real-world" distribution shift.
* **Correction:** Re-classified explicitly as "parametric distribution shifts within the V2 synthetic data-generating framework." V2A, V2B, and V2C all stem from the identical generator; the observed survival merely proves the model is insensitive to global volume parameter reductions.

## 5. Final Scientifically Defensible Interpretation
The engineering hygiene (leakage prevention, schema reconstruction) was executed flawlessly. However, the evaluation remains strictly synthetic-on-synthetic. 

**Final Decision: MODERATE CROSS-UNIVERSE GENERALIZATION**
The model is robust to internal parameter shifts within the synthetic framework and successfully preserves its P@1% operational baseline. However, trivial hard-negative separation and the lack of real-world validation prevent any stronger claims of deployment readiness.
