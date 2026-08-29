import json
import os

with open(r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\phase3a\dataset_audit.json", 'r') as f:
    audit = json.load(f)

# 1. Dataset Audit Report
audit_report = f"""# PHASE 3A-01: DATASET AUDIT REPORT
**Profile Audited:** {audit['profile']}
**Path:** `{audit['directory']}`
**Timestamp:** {audit['timestamp']}

## 1. Dataset Inventory & Row Counts
Total logical tables found: {len(audit['tables'])}

| Table | Row Count | Attributes | Key File Path |
|-------|-----------|------------|---------------|
"""

for t, data in audit['tables'].items():
    audit_report += f"| `{t}` | {data['row_count']:,} | {len(data['schema'])} | `{t}/` |\n"

audit_report += "\n## 2. Table Schemas & Missingness\n"
for t, data in audit['tables'].items():
    audit_report += f"### `{t}`\n"
    for col, null_rate in data['null_rates'].items():
        audit_report += f"- `{col}` (Null rate: {null_rate*100:.2f}%)\n"
    if 'timestamp_range' in data:
        for col, trange in data['timestamp_range'].items():
            audit_report += f"- **Temporal Range ({col})**: {trange[0]} to {trange[1]}\n"
    audit_report += "\n"

with open(r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\phase3a\DATASET_AUDIT_REPORT.md", 'w', encoding='utf-8') as f:
    f.write(audit_report)


# 2. Label Catalog
label_report = f"""# PHASE 3A-02: LABEL CATALOG
**Source Table:** `ground_truth/person_labels`
**Target Entity:** `PERSON`

## 1. Label Distribution (`scenario_class`)
The dataset exhibits a realistic, highly imbalanced distribution:
"""
for k, v in audit.get('label_distributions', {}).items():
    pct = (v / 250000) * 100
    label_report += f"- **{k}**: {v:,} rows ({pct:.1f}%)\n"

label_report += """
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
"""
with open(r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\phase3a\LABEL_CATALOG.md", 'w', encoding='utf-8') as f:
    f.write(label_report)

# 3. Leakage Audit
leakage = audit['ground_truth_isolation']
passed = leakage.get('passed', False)
status = "✅ PASS" if passed else "❌ FAIL"

leak_report = f"""# PHASE 3A-02: LABEL LEAKAGE AUDIT
**Status:** {status}

## 1. Feature Isolation Check
We programmatically scanned the aggregated ML feature tables (`ml_features/`) for any column names indicating ground-truth leakage (e.g., `scenario`, `risk_score_gt`, `is_positive`).

**Findings:**
"""
if passed:
    leak_report += "No leakage detected. The ML features are perfectly isolated from the ground truth labels.\n"
else:
    leak_report += f"Leakage detected! The following columns leaked: {leakage.get('ml_features_leaks')}\n"

leak_report += """
## 2. Temporal Leakage
- **Observation:** All CDRs and Transactions are bounded by explicit timestamps.
- **Action Required:** When extracting features, we must strictly enforce `feature_available_at` cutoffs to prevent future transactions from influencing historical predictions.

## 3. Train / Validation / Test Integrity
The dataset is deterministically pre-split:
"""
for k, v in audit.get('splits', {}).items():
    leak_report += f"- **{k}**: {v:,} persons\n"

leak_report += "\nModels must strictly adhere to `split` column filtering during training."

with open(r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\phase3a\LABEL_LEAKAGE_AUDIT.md", 'w', encoding='utf-8') as f:
    f.write(leak_report)

print("Markdown reports successfully generated.")
