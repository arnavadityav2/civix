# CIVIX Phase 5: GNN Research Branch

## 1. Purpose
The Graph Neural Network (GNN) branch investigates whether graph-based message passing (specifically GraphSAGE) provides additional predictive signal beyond the standard topological aggregates and behavioral features utilized by the tree-based ML pipeline.

## 2. Current Status
**FROZEN FOR FUTURE RESEARCH**

The GNN is **NOT** the current production model. The research branch is temporarily frozen until a compatible full-topology sampling environment can be established. 

## 3. Current Production Candidate
Behavioral XGBoost remains the strongest, unchallenged model evaluated so far and serves as the Phase 5 production candidate.
* **Behavioral XGBoost PR-AUC:** 0.5726
* **Behavioral XGBoost ROC-AUC:** 0.8646

## 4. Experiment Summary

| Experiment | Graph | Features | Result | Status |
|------------|-------|----------|--------|--------|
| **Exp 1** | 5M DropEdge | Raw | PR-AUC 0.1019 | Failed numerical stability (majority-class collapse) |
| **Exp 2** | 5M DropEdge | Stabilized | PR-AUC 0.1211 | Completed (Weak signal recovered after stabilization) |
| **Exp 3** | 63.3M + NeighborLoader | Stabilized | No metrics | **ABORTED** (Environment / Dependency Limitation) |

* **Experiment 1** collapsed due to extreme feature magnitudes (unscaled logits exceeding 400M) and a lack of positive class weighting.
* **Experiment 2** successfully applied stabilization (`StandardScaler`, class weighting, `LayerNorm`, gradient clipping), preventing collapse and extracting genuine, albeit weak, structural signal. However, it was strictly limited to a randomly sampled 5M-edge subset, severely destroying graph topology.
* **Experiment 3** was designed to evaluate full-topology neighborhood sampling on the canonical 63.3M edges using PyTorch Geometric's `NeighborLoader`. It was aborted during the pre-flight Memory Smoke Test because the environment lacked the required compiled C++ dependencies (`pyg-lib` or `torch-sparse`).

## 5. Documenting What Remains Unknown
**Whether GraphSAGE can extract substantially stronger signal from the complete 63.3M-edge CIVIX graph remains unresolved.**

The current experiments do not provide a fair full-topology GraphSAGE evaluation. The DropEdge constraint imposed on Exp 2 artificially isolated neighborhoods, and Exp 3 could not be executed to test the alternative. 

The Graph-only Random Forest baseline (PR-AUC: 0.1507, ROC-AUC: 0.6222) conclusively demonstrates that the 108M-edge graph *does* contain predictive structural signal. We simply do not yet know if a GNN can exceed this baseline if given proper topological access.

## 6. Pre-Flight Degree Audit (Exp 3)
Before Exp 3 was aborted, the pre-flight script successfully audited the complete 63.3M-edge canonical topology. This evidence is critical for future research, as it proves that criminal entities are NOT topologically isolated.

**Positive Nodes (Criminals):**
* Minimum degree: 192
* Median degree: 466.0
* Mean degree: 515.9
* 90th percentile: 775
* 95th percentile: 924
* 99th percentile: 1273
* Maximum degree: 1714
* Degree 0: 0.00%
* Degree <= 10: 0.00%

**Negative Nodes (Baselines):**
* Minimum degree: 159
* Median degree: 430.0
* Mean degree: 506.0
* 90th percentile: 828
* 95th percentile: 1102
* 99th percentile: 1446
* Maximum degree: 1868
* Degree 0: 0.00%
* Degree <= 10: 0.00%

## 7. Configuration and Reproducibility Information
If reproducing Experiment 2 or resuming Experiment 3, the following configuration MUST be adhered to:
* **Random Seed:** 42 (Controls PyTorch, PyG sampling, and DropEdge initialization)
* **Dataset Version:** V2A (250,000 nodes, 63,370,696 canonical edges)
* **Feature Scaling:** `StandardScaler` (Must be fitted strictly on the TRAIN split)
* **Class Weighting:** 8.99x (Positive class weight)
* **Architecture:** 2 Layers (SAGEConv -> LayerNorm -> ReLU -> Dropout)
* **Hidden Dimensions:** 64
* **Neighbor Fanout (Exp 3):** [15, 10]
* **Learning Rate:** 5e-4
* **Epochs:** 30 maximum
* **Gradient Clipping:** `max_norm=1.0`
* **Device:** CPU
* **PyTorch Geometric Version:** 2.6.x (UNKNOWN C++ Bindings)

## 8. Model Artifacts
Artifacts are preserved in their original generating directories to maintain pipeline integrity:
* **GNN Architecture:** `civix_ml/models/gnn.py`
* **Exp 1 / 2 Scripts:** `scratch/run_experiment2.py`, `scratch/audit_gnn_run1.py`
* **Exp 3 Script:** `scratch/gnn_exp3_prep.py`
* **Exp 2 Report:** `docs/phase5/GNN_EXPERIMENT_2_REPORT.md`
* **Exp 3 Config:** `docs/phase5/GNN_EXP3_CONFIGURATION.md`
* **Exp 3 Degree Audit:** `docs/phase5/GNN_EXP3_DEGREE_AUDIT.md`
* **Exp 3 Smoke Test Failure:** `docs/phase5/GNN_EXP3_MEMORY_SMOKE_TEST.md`
* **Exp 3 Final Analysis:** `docs/phase5/GNN_EXP3_FINAL_ANALYSIS.md`
* **Model Checkpoints:** Saved natively alongside standard ML artifacts in `[config.MODELS_DIR]/registry/`

## 9. Production Safety
The GNN branch is completely isolated from the production ML pipeline. 
* The production model selection uses XGBoost.
* The API, dashboard, and backend inference loops do NOT import `civix_ml/models/gnn.py`.
* PyTorch Geometric is NOT a required dependency for the production risk scoring pipeline.

## 10. Future GNN Reattempt
When GNN research resumes, the first priority is **NOT** blindly tuning the model or modifying the architecture. The first priority is obtaining a valid full-topology sampling environment.

**Potential future approaches:**
1. Linux/WSL environment with compatible PyG compiled dependencies
2. Compatible `pyg-lib` installation
3. Compatible `torch-sparse` installation
4. NVIDIA GPU environment
5. Higher-RAM machine (to bypass sampling and use full-batch)
6. Alternative graph sampling implementation (e.g., DGL)
7. Alternative GNN architecture
8. Custom out-of-core graph sampling if necessary

*Do not install or modify any of these during the Phase 5 Prototype build.*

## 11. Future Experiment Requirements
The next GNN experiment MUST preserve the following scientific constraints:
* Canonical 63.3M-edge graph (No DropEdge truncation).
* Entity-isolated Train/Validation/Test split.
* Train-only feature scaling (No test leakage).
* Fixed random seed (42).
* Explicit memory profiling.
* Degree-distribution audit.
* PR-AUC, ROC-AUC, P@1%, R@1%, F1 evaluation.
* Hard-negative evaluation.
* Strict A/B comparison against Graph-only RF and Behavioral XGBoost.

**Important Limitation:** Neighbor sampling is still an approximation of full message passing. A fanout of `[15,10]` does NOT mean the model sees every neighbor of every node in every layer. This topological limitation must be explicitly acknowledged in all future reports.
