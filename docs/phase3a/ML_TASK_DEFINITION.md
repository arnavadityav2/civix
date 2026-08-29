# PHASE 3A: ML TASK DEFINITION
**Target:** Profile C
**Date:** 2026-08-29

Based on the actual labels available in `ground_truth/person_labels` and the available features (75M CDRs, 18M transactions, geographic movement), we will execute the following ML tasks for Phase 3A.

## 1. TASK A — Suspicious Entity Classification (Primary)
**Goal:** Classify if an entity exhibits genuinely suspicious behavioral patterns.
**Target Variable:** `is_positive_label` (Boolean)
**Classes:**
- `0` (Negative): Normal + Suspicious + False Positive (90% of dataset)
- `1` (Positive): Confirmed Pattern (10% of dataset)
**Business Value:** This acts as the primary "risk score" generator for investigators.

## 2. TASK B — Hard Negative Discrimination
**Goal:** Distinguish between entities that look identical in volume (high calls/txns) but differ in intent.
**Target Variable:** `is_false_positive` (Boolean)
**Dataset Subset:** Train/Evaluate *only* on the subset of data where activity volume > 95th percentile.
**Business Value:** Reduces alert fatigue by suppressing alerts for legitimate businesses, call centers, and highly-active joint accounts.

## 3. TASK C — Graph Link Prediction (Future/GNN Phase)
**Goal:** Predict unobserved or hidden relationships between entities.
**Target Variable:** Edge existence (`1` = true relationship, `0` = negative sample).
**Business Value:** Discovers hidden accomplices or burner phones that have not yet directly communicated with a known suspect.

## 4. TASK D — Investigative Priority Ranking
**Goal:** Produce a continuous score [0, 1] ranking entities for investigation.
**Target Variable:** Synthesized continuous risk score calibrated via Platt Scaling from Task A logits.
**Business Value:** Feeds the UI dashboard, allowing officers to sort cases and persons by mathematical priority.

---
*Note: We will NOT implement multi-class scenario identification (predicting exactly which of the 69 crime patterns is occurring) in Phase 3A, as this requires significantly more feature engineering. We will stick to binary risk scoring (Task A) to establish baselines.*
