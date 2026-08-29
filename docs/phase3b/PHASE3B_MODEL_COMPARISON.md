# CIVIX Phase 3B — Three-Way Model Comparison

> Comparison of behavioral-only, graph-only, and combined feature sets.

> PR-AUC is the primary metric. Isolation Forest is the only unsupervised model.

| feature_set   | model            |   pr_auc |   roc_auc |   p_at_1pct |   r_at_1pct |       f1 |   fp_rate |   n_features | error                                                     |
|:--------------|:-----------------|---------:|----------:|------------:|------------:|---------:|----------:|-------------:|:----------------------------------------------------------|
| behavioral    | logistic         |   0.4996 |    0.8319 |      0.896  |      0.0879 |   0.4042 |    0.2048 |           60 | nan                                                       |
| behavioral    | random_forest    |   0.5225 |    0.8454 |      0.888  |      0.0871 |   0.4678 |    0.1269 |           60 | nan                                                       |
| behavioral    | xgboost          |   0.5726 |    0.8646 |      0.936  |      0.0918 |   0.4824 |    0.1367 |           60 | nan                                                       |
| behavioral    | isolation_forest | nan      |  nan      |    nan      |    nan      | nan      |  nan      |          nan | y_prob contains values greater than 1: 1.043885347396038  |
| graph         | logistic         |   0.1433 |    0.6086 |      0.1947 |      0.0191 |   0.2161 |    0.4724 |           25 | nan                                                       |
| graph         | random_forest    |   0.1507 |    0.6222 |      0.2293 |      0.0225 |   0.2246 |    0.3801 |           25 | nan                                                       |
| graph         | xgboost          |   0.1501 |    0.6237 |      0.208  |      0.0204 |   0.227  |    0.4112 |           25 | nan                                                       |
| graph         | isolation_forest |   0.0951 |    0.49   |      0.0453 |      0.0044 |   0.0525 |    0.0705 |           25 | nan                                                       |
| combined      | logistic         |   0.503  |    0.8322 |      0.8987 |      0.0882 |   0.4078 |    0.1995 |           85 | nan                                                       |
| combined      | random_forest    |   0.5219 |    0.844  |      0.8987 |      0.0882 |   0.4689 |    0.1254 |           85 | nan                                                       |
| combined      | xgboost          |   0.5737 |    0.8655 |      0.9307 |      0.0913 |   0.4841 |    0.1351 |           85 | nan                                                       |
| combined      | isolation_forest | nan      |  nan      |    nan      |    nan      | nan      |  nan      |          nan | y_prob contains values greater than 1: 1.0000000000000002 |

## Interpretation
- If graph-only PR-AUC > behavioral-only: graph topology provides independent signal.
- If combined > both: graph and behavioral are complementary.
- If supervised models achieve 1.0: synthetic separability artifact — check artifact audit before celebrating.
