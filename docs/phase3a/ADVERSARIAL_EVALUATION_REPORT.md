# CIVIX Phase 3A — Adversarial Evaluation Report

## isolation_forest

### overall
```json
{
  "model": "isolation_forest",
  "pr_auc": 0.5249,
  "roc_auc": 0.9172,
  "precision": 0.6371,
  "recall": 0.2201,
  "f1": 0.3272,
  "brier_score": 0.174,
  "false_positive_rate": 0.0141,
  "false_negative_rate": 0.7799,
  "confusion_matrix": [
    [
      33236,
      475
    ],
    [
      2955,
      834
    ]
  ],
  "threshold": 0.5,
  "n_positives": 3789,
  "n_total": 37500,
  "precision_at_1pct": 0.808,
  "recall_at_1pct": 0.08,
  "precision_at_5pct": 0.5835,
  "recall_at_5pct": 0.2887,
  "precision_at_10pct": 0.4936,
  "recall_at_10pct": 0.4885
}
```

- **false_positive_flag_rate**: 0.115
- **false_positive_avg_score**: 0.4547
- **high_call_volume_fp_rate**: 0.1706
- **confirmed_precision_at_50pct**: 1.0

## logistic_regression

### overall
```json
{
  "model": "logistic_regression",
  "pr_auc": 1.0,
  "roc_auc": 1.0,
  "precision": 1.0,
  "recall": 1.0,
  "f1": 1.0,
  "brier_score": 0.0,
  "false_positive_rate": 0.0,
  "false_negative_rate": 0.0,
  "confusion_matrix": [
    [
      33711,
      0
    ],
    [
      0,
      3789
    ]
  ],
  "threshold": 0.5,
  "n_positives": 3789,
  "n_total": 37500,
  "precision_at_1pct": 1.0,
  "recall_at_1pct": 0.099,
  "precision_at_5pct": 1.0,
  "recall_at_5pct": 0.4949,
  "precision_at_10pct": 1.0,
  "recall_at_10pct": 0.9897
}
```

- **false_positive_flag_rate**: 0.0
- **false_positive_avg_score**: 0.0002
- **high_call_volume_fp_rate**: 0.0
- **confirmed_precision_at_50pct**: 1.0

## random_forest

### overall
```json
{
  "model": "random_forest",
  "pr_auc": 1.0,
  "roc_auc": 1.0,
  "precision": 1.0,
  "recall": 1.0,
  "f1": 1.0,
  "brier_score": 0.0001,
  "false_positive_rate": 0.0,
  "false_negative_rate": 0.0,
  "confusion_matrix": [
    [
      33711,
      0
    ],
    [
      0,
      3789
    ]
  ],
  "threshold": 0.5,
  "n_positives": 3789,
  "n_total": 37500,
  "precision_at_1pct": 1.0,
  "recall_at_1pct": 0.099,
  "precision_at_5pct": 1.0,
  "recall_at_5pct": 0.4949,
  "precision_at_10pct": 1.0,
  "recall_at_10pct": 0.9897
}
```

- **false_positive_flag_rate**: 0.0
- **false_positive_avg_score**: 0.0314
- **high_call_volume_fp_rate**: 0.0
- **confirmed_precision_at_50pct**: 1.0

## xgboost

### overall
```json
{
  "model": "xgboost",
  "pr_auc": 1.0,
  "roc_auc": 1.0,
  "precision": 1.0,
  "recall": 1.0,
  "f1": 1.0,
  "brier_score": 0.2037,
  "false_positive_rate": 0.0,
  "false_negative_rate": 0.0,
  "confusion_matrix": [
    [
      33711,
      0
    ],
    [
      0,
      3789
    ]
  ],
  "threshold": 0.5,
  "n_positives": 3789,
  "n_total": 37500,
  "precision_at_1pct": 1.0,
  "recall_at_1pct": 0.099,
  "precision_at_5pct": 1.0,
  "recall_at_5pct": 0.4949,
  "precision_at_10pct": 1.0,
  "recall_at_10pct": 0.9897
}
```

- **false_positive_flag_rate**: 0.0
- **false_positive_avg_score**: 0.4513
- **high_call_volume_fp_rate**: 0.0
- **confirmed_precision_at_50pct**: 1.0

