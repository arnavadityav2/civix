# CIVIX Phase 5 (Chunk 1C) — Baseline Model Report
**Date:** 2026-08-29  
**Dataset:** `profile_v2_v2a` (Synthetic World V2)  
**Evaluation Type:** Retrospective Final-Outcome Classification (Predicting 2024-12-31 status)

> [!WARNING]  
> **RETROSPECTIVE EVALUATION**  
> These metrics represent final 3-year outcomes using a single entity-isolated Test split. Because genuine point-in-time label onsets do not exist in V2, these results must **not** be presented as real-time, early-warning, or deployment-ready capabilities.

## 1. Dataset Dimensions
- **Train Set:** 175,000 entities
- **Test Set:** 37,500 entities
- **Features:** 71 non-leaky behavioral metrics

## 2. Model Performance (Test Set)

| Model | ROC-AUC | PR-AUC | F1 Score | P@1% | R@1% | P@5% | R@5% |
|-------|---------|--------|----------|------|------|------|------|
| Logistic Regression | 0.8351 | 0.5022 | 0.4108 | 0.8907 | 0.0874 | 0.6661 | 0.3268 |
| Random Forest | 0.8406 | 0.5138 | 0.4492 | 0.8827 | 0.0866 | 0.6816 | 0.3344 |

*(Note: XGBoost bypassed due to environmental execution limitations).*

### Unsupervised Reference (Isolation Forest)
- **Precision:** 0.1048
- **Recall:** 0.1026
- **F1 Score:** 0.1037
- **Confusion Matrix:** TN=30331, FP=3347, FN=3430, TP=392

## 3. Artifact Scan & Feature Integrity

In Phase 3A, supervised models trivially achieved PR-AUC 1.0 due to generator artifacts (zero-variance hardcoded constants). 

**V2 Analysis:**
- Supervised PR-AUC dropped from 1.0 to **~0.51**. 
- ROC-AUC sits at a realistic **~0.84**.
- Top features are high-variance behavioral aggregations (`calls_per_active_day`, `night_call_ratio`, `geo_spread_degrees`), not arbitrary fixed constants.

**Conclusion:** The models **did not** produce near-perfect performance. The V2 generator successfully removed the blatant synthetic artifacts present in V1. The dataset now requires the models to learn genuine statistical overlaps between normal and criminal behavior.

## 4. Top Feature Importances

**Random Forest:**
1. `calls_per_active_day` (0.228)
2. `night_call_ratio` (0.087)
3. `active_days` (0.057)
4. `location_active_days` (0.056)
5. `night_call_count` (0.052)

**Logistic Regression (Abs Coef):**
1. `calls_per_active_day` (4.73)
2. `voice_calls` (3.25)
3. `total_calls` (2.48)
4. `night_call_count` (1.44)
5. `sms_count` (1.38)

*Insight:* Both models are heavily indexing on **call volume density** and **nighttime activity** as the primary discriminators of the `confirmed_pattern` class.
