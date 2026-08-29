# CIVIX Phase 3A — Baseline Model Report (TEST SET)

> All metrics computed on the held-out TEST split (37,500 persons).

| model   |   pr_auc |   roc_auc |   precision |   recall |     f1 |   precision_at_1pct |   recall_at_1pct |   precision_at_5pct |   recall_at_5pct |   false_positive_rate |   brier_score |
|:--------|---------:|----------:|------------:|---------:|-------:|--------------------:|-----------------:|--------------------:|-----------------:|----------------------:|--------------:|
| xgboost |   0.5484 |    0.8488 |       0.404 |   0.6372 | 0.4945 |                0.92 |           0.0897 |              0.7253 |           0.3537 |                0.1074 |         0.113 |