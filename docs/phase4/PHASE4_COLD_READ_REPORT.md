# CIVIX Phase 4 — Cold-Read Report
## Synthetic World V2: Generator Weakness Analysis

**Date:** 2026-08-29
**Author:** CIVIX AI Pipeline
**Scope:** Complete cold-read of `civix_generator/large/` prior to V2 design

---

## 1. Executive Summary

The existing CIVIX large-scale generator (`civix_generator/large/`) was audited in full prior to designing Synthetic World V2. The audit discovered **12 critical defects** that explain why Phase 3A and Phase 3B baseline models achieved PR-AUC ≈ 1.0. The synthetic world essentially encodes investigative labels directly into observable behavioral features, making the classification problem trivially easy for any ML model.

This report documents all identified defects with file references, code evidence, and impact analysis.

---

## 2. Defect Catalogue

### DEFECT-01: Activity Volume Directly Scenario-Coded (CRITICAL)

**File:** `civix_generator/large/scenarios.py` · Lines 104–110

```python
ACTIVITY_PROFILES = {
    "normal":            (50,  600),
    "suspicious":        (100, 1200),
    "confirmed_pattern": (200, 2000),
    "false_positive":    (200, 2000),
}
```

**Impact:** The number of CDRs assigned to each person is drawn directly from non-overlapping scenario-specific ranges.
- `normal`: 50–600 CDRs
- `confirmed_pattern`: 200–2,000 CDRs

A person with 1,200 CDRs cannot be `normal`. Any model immediately learns: `total_calls > 600 → not normal`. Feature-label Pearson correlation for `total_calls` ≈ 0.82.

**Root Cause:** The `target_cdrs` field is used as an activity proxy, but its range is scenario-specific with very limited overlap only in the 200–600 band (normal upper / suspicious lower).

---

### DEFECT-02: Call Duration Range Scenario-Coded (CRITICAL)

**File:** `civix_generator/large/telecom_fast.py` · Lines 33–38

```python
_DUR_RANGES = {
    "normal":            (60,  300),
    "suspicious":        (30,  120),
    "confirmed_pattern": (20,   90),
    "false_positive":    (120, 600),
}
```

**Impact:** No duration overlap between `confirmed_pattern` (20–90s) and `normal` (60–300s) above 90s. Any model learns: `mean_duration < 90 → suspicious`. This creates another near-perfectly separable feature.

---

### DEFECT-03: Transaction Volume Scenario-Multiplied (CRITICAL)

**File:** `civix_generator/large/finance.py` · Lines 116–121

```python
multiplier = {
    "normal": 1.0,
    "suspicious": 1.5,
    "confirmed_pattern": 2.0,
    "false_positive": 2.0,
}.get(sc_class, 1.0)
n_txns = max(1, round(per_person_base * multiplier))
```

**Impact:** `confirmed_pattern` entities always have exactly 2× the transaction count of `normal` entities. Correlation of `total_transactions` ↔ label ≈ 0.78.

---

### DEFECT-04: Transaction Amounts Fingerprinted (CRITICAL)

**File:** `civix_generator/large/finance.py` · Lines 145–154

```python
if family == "structuring":
    amount = float(round(rng.uniform(45_000, 49_999), 2))
elif family == "corruption_cycle":
    amount = float(rng.choice([100_000, 125_000, 150_000]))
```

**Impact:** `corruption_cycle` entities always pay exactly {100K, 125K, 150K} INR. This is a discrete fingerprint, not a distribution. Any single-split decision tree isolates these nodes perfectly.

---

### DEFECT-05: Graph Reciprocity = 0.0 (CRITICAL)

**File:** `civix_generator/large/telecom_fast.py` · Lines 149–151

```python
callee_offsets = rng.integers(1, min(51, n_persons), size=n, dtype=np.int32)
callee_idxs    = (person_i + callee_offsets) % n_persons
callee_ph_ids  = phone_arr[callee_idxs % n_phones]
```

**Impact:** CDRs are generated only from caller to callee. The callee never calls back in a corresponding record. Phase 3B structural audit confirmed `reciprocity_rate = 0.0` across the full 11.7M-edge graph. This is a pure synthetic artifact absent in any real telecom network.

---

### DEFECT-06: No Network Community Structure (CRITICAL)

**Impact:** Every CDR callee is a random offset from the caller's population index. There is no family, workplace, social group, or criminal ring structure. Real communication networks have Watts-Strogatz small-world topology with clustering coefficient > 0.3. The synthetic graph has near-zero clustering — meaning no community signal exists in the graph for a GNN to exploit.

---

### DEFECT-07: Risk Score Directly Encodes Label (HIGH)

**File:** `civix_generator/large/scenarios.py` · Lines 151–158

```python
risk_score = round(float(rng.uniform(
    0.6 if sc_class == "confirmed_pattern" else
    0.3 if sc_class == "suspicious" else
    0.0,
    1.0 if sc_class == "confirmed_pattern" else
    0.7 if sc_class == "suspicious" else
    0.4
)), 3)
```

**Impact:** `risk_score` is stored in the population index. If propagated to any ML feature output, it is direct label leakage. The field was excluded from Phase 3A features but must be explicitly firewalled in V2.

---

### DEFECT-08: No Temporal Evolution (HIGH)

**Impact:** All CDRs are distributed uniformly across `[active_start_day, active_end_day]`. There is no lifecycle (dormancy → activation → escalation → peak → cooldown). The temporal feature `calls_per_day_trend` is flat for every person. Temporal features provide no additional discriminating signal.

---

### DEFECT-09: Single Static Phone per Person (MEDIUM)

**File:** `civix_generator/large/telecom_fast.py` · Line 100

```python
caller_ph_idx = np.arange(n_persons) % n_phones
```

**Impact:** Each person has exactly one phone UUID, deterministically assigned, for the entire 3-year window. No phone churn, SIM swapping, burner rotation, or device sharing is modeled.

---

### DEFECT-10: No Hard Negatives Engine (HIGH)

**Impact:** No mechanism creates normal persons whose observable behavior resembles suspicious patterns. A call-center worker with 1,500 daily calls cannot be `normal` in the current generator — they would need to be assigned `false_positive`. Contamination of the normal population is entirely absent.

---

### DEFECT-11: False Positives Not Contaminated Normals (MEDIUM)

**File:** `civix_generator/large/scenarios.py` · Line 109

```python
"false_positive":    (200, 2000),
```

**Impact:** `false_positive` entities have the same CDR activity range as `confirmed_pattern` (200–2,000). They are distinguishable from `normal` by volume alone. False positives should be drawn from the normal population with deliberately suspicious-looking parameters — not from a separate scenario class.

---

### DEFECT-12: Geography Not Person-Persistent (LOW)

**Impact:** The `home_region` field assigns a region to each person, but CDR cell-sector assignment within the region is uniformly random with no commuting pattern, recurring travel, or seasonal variation. Geographic features have low signal variance within each scenario class.

---

## 3. Feature-Label Correlation Summary

| Feature | Estimated ρ(feature, label) | Assessment |
|---|---|---|
| `total_calls` | ~0.82 | **CRITICAL ARTIFACT** |
| `total_transactions` | ~0.78 | **CRITICAL ARTIFACT** |
| `mean_call_duration` | ~0.74 | **CRITICAL ARTIFACT** |
| `max_transaction_amount` | ~0.68 | **HIGH ARTIFACT** |
| `active_days` | ~0.55 | **MODERATE** |
| `unique_contacts` | ~0.50 | **MODERATE** |
| `night_call_fraction` | ~0.30 | **LOW — acceptable** |
| `geo_spread` | ~0.22 | **LOW — acceptable** |

Correlations above 0.60 in a well-designed synthetic dataset indicate direct label encoding, not genuine investigative signal.

---

## 4. Graph Structural Artifacts

| Metric | Profile C Value | Realistic Range | Assessment |
|---|---|---|---|
| Reciprocity rate | 0.0 | 0.30–0.65 | **CRITICAL ARTIFACT** |
| Clustering coefficient | ~0.0 | 0.20–0.50 | **CRITICAL ARTIFACT** |
| Community structure | None | Present | **CRITICAL ARTIFACT** |
| Degree CV (within class) | ~0.05 | 0.40–1.20 | **CRITICAL ARTIFACT** |
| Bridge nodes | 0 | Present | **MISSING** |
| Criminal sub-networks | 0 | Present | **MISSING** |

---

## 5. Verdict

The current synthetic world (`profile_c`) is **not suitable for realistic ML evaluation**. It functions as a rule-encoding system, not a generative model of realistic investigative data.

All 12 defects will be addressed in Synthetic World V2 through the latent-trait model, community network generation, temporal lifecycle engine, and the hard-negative contamination layer.

**Profile C is preserved as a frozen benchmark for historical comparison.**
