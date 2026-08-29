# PHASE 3A-02: LABEL CATALOG
**Source Table:** `ground_truth/person_labels`
**Target Entity:** `PERSON`

## 1. Label Distribution (`scenario_class`)
The dataset exhibits a realistic, highly imbalanced distribution:
- **normal**: 174,865 rows (69.9%)
- **suspicious**: 37,433 rows (15.0%)
- **false_positive**: 12,653 rows (5.1%)
- **confirmed_pattern**: 25,049 rows (10.0%)

## 2. Recommended Prediction Tasks
Based on the dataset audit, the following ML tasks are legitimately supported:

### A. Binary Suspicious Activity Detection (Primary)
- **Target:** `is_positive_label` (Boolean)
- **Positive Class:** `confirmed_pattern` (10%)
- **Negative Class:** `normal`, `suspicious`, `false_positive` (90%)
- **Rationale:** Simulates real-world "is this entity genuinely criminal?" flagging.

### B. Hard-Negative Discrimination
- **Target:** Differentiate `confirmed_pattern` from `false_positive`
- **Rationale:** Teaches the model to ignore entities that look guilty but are actually benign (e.g. frequent callers, shared legitimate devices).

### C. Multi-class Scenario Detection
- **Target:** `scenario_family`
- **Rationale:** Identifies *what kind* of anomaly is occurring (e.g., money laundering vs trafficking).
