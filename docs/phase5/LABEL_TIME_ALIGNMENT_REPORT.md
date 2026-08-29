# V2 Label-Time Alignment Report (Chunk 1B)
**Date:** 2026-08-29  
**Phase:** 5 (Chunk 1B Audit)  
**Dataset:** `profile_v2_v2a`  

---

## 1. Executive Conclusion

> [!WARNING]
> **B. POINT-IN-TIME NOT FEASIBLE — RETROSPECTIVE EVALUATION**
>
> The existing V2A dataset **does not** contain genuine label-onset timestamps. The `scenario_class` target label is assigned as a static, final-outcome status that applies to the entire 3-year simulation window, irrespective of when the entity actually escalated their behavior. 
> 
> Therefore, Phase 5 cannot be claimed as a true "real-time point-in-time" predictive evaluation. It must be explicitly classified and documented as a **Retrospective / Final-Outcome Evaluation**.

---

## 2. Evidence of Non-Temporal Labels

An exhaustive audit of the V2 dataset architecture and ground-truth output parquet files reveals the following:

### A. Ground-Truth Schema
The table `D:\civix_data\synthetic\profile_v2_v2a\ground_truth\person_labels\*.parquet` contains the exact target labels but completely lacks temporal boundaries:
- `scenario_class`
- `is_positive_label`
- `is_false_positive`
- `in_criminal_network`
*Result: 0 temporal onset / expiration columns found.*

### B. Generator State-Machine
Inspection of `civix_generator/v2/temporal_engine.py` and `civix_generator/v2/ground_truth.py` confirms:
1. `is_positive_label` is determined strictly by the static hidden state (membership in a criminal community at world initialization).
2. The temporal engine creates changing behavioral phases (e.g., `baseline` → `activation` → `escalation` → `peak`).
3. **Crucial Disconnect:** The generator does *not* log the exact timestamp when a person "officially" crossed the threshold into becoming suspicious or confirmed.

### C. Case Study Example
**Entity ID:** `9f7f344b-893d-5416-f84c-756b24d8827e`
**Static Label:** `confirmed_pattern`
**Behavioral Timeline (Monthly CDR Count):**
- 2022-03: 6 calls (Baseline/Dormant)
- 2022-07: 18 calls (Baseline/Dormant)
- 2023-01: 14 calls (Baseline/Dormant)
- 2023-11: 41 calls (Escalation)
- **2023-12: 79 calls (Peak Burst)**
- 2024-01: 56 calls (Peak)
- 2024-11: 1 call (Cooldown)

**The Problem:**
If we construct a temporal split using `as_of_timestamp = 2022-12-31`, this person's features would reflect only standard baseline behavior. However, their ground-truth label would still be joined as `confirmed_pattern`. This forces the ML model to retroactively guess future outcomes from normal baseline data, which corrupts the objective of "real-time detection."

---

## 3. Quantitative Summary

| Metric | Result |
|--------|--------|
| Total Entities | 250,000 |
| Entities with Label Onset Timestamps | **0** |
| Entities without Label Onset Timestamps | 250,000 |
| Percentage Temporally Alignable | **0.0%** |
| Label Mutability | Static (Whole-Window) |

---

## 4. Remediation & Mandatory Rules for Phase 5

Because true label onset timestamps do not exist, we will **NOT fabricate them**. 

To preserve the integrity of the evaluation, the following rules are now in effect for the remainder of Phase 5:

1. **Classification:** All models trained on V2A will be explicitly labelled as predicting the **"Final 3-Year Outcome"** (Retrospective), not "Current Point-in-Time Status".
2. **Temporal Split Abandonment:** We will abandon Step 5 (Chronological Splits). Because the labels represent the 2024-12-31 final outcome, training on 2022 data with 2024 labels is statistically invalid and constitutes future leakage. 
3. **Split Strategy:** We will strictly rely on entity-isolated splits (Train/Val/Test) where features are aggregated up to `2024-12-31` for all entities, predicting their final status.
7. **No Deployment Claims:** Results on this dataset must never be presented as proof of real-time operational deployment capability.

---

## 5. GATE 5 — Label-Time Alignment Check

**Feature temporal integrity:** features contain no events after 2024-12-31.
**Label temporal integrity:** labels represent final whole-window outcomes and have no onset timestamps.
**Evaluation type:** retrospective final-outcome classification.

**STATUS:** Audit and Gate 5 complete. Proceeding to Chunk 1C.
