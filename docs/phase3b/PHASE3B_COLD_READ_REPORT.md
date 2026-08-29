# PHASE 3B: COLD READ & RECONCILIATION REPORT
**Target:** Profile C (Graph Intelligence Pipeline)
**Date:** 2026-08-29

## 1. Existing Graph-Relevant Data (Profile C)
The canonical dataset located at `D:\civix_data\synthetic\profile_c` contains elements natively suited for heterogeneous graph construction:
- **Nodes**: Persons (250,000), Phones, SIMs, Devices (~1.2M), Accounts, Cell Sectors (8,000), Cases (25,000), Locations (15,000).
- **Edges (Temporal)**: 75M CDRs (Call Detail Records linking caller -> callee phones/persons), 18.38M Transactions (linking sender -> receiver accounts/persons).
- **Edges (Static)**: Implied ownership edges (Person -> Phone/SIM/Device/Account), locational edges (Person -> Cell Sector via CDR), case involvement.

## 2. Existing Features, Labels, and Splits
- **Features**: Phase 3A successfully built 70 behavioral features (after dropping 11 generator artifacts).
- **Labels**: Isolated in `ground_truth/person_labels/*.parquet`. Scenarios are: `normal`, `suspicious`, `confirmed_pattern` (positive class), `false_positive`.
- **Splits**: Pre-computed splits exist and must be preserved: TRAIN (175,000), VALIDATION (37,500), TEST (37,500).
- **Temporal Boundaries**: Dataset spans 2022-01-01 to 2024-12-31. Strict temporal leakage protection (`as_of_timestamp=2024-12-31`) must be maintained.

## 3. Phase 3A Limitations & Generator Artifacts
- **Artifacts Discovered**: 11 features had near-zero within-class variance due to the synthetic generator hardcoding fixed constants per scenario (e.g., `total_txns`, `avg_duration_sec`). These were dropped.
- **Synthetic Separability**: Despite dropping the 11 artifacts, supervised baselines (Logistic, RF, XGBoost) scored PR-AUC=1.0000 on the TEST set. This is because the remaining 65 overlapping behavioral features, when combined, create perfectly separable multidimensional clusters characteristic of synthetic generation.
- **Honest Benchmark**: The unsupervised Isolation Forest scored PR-AUC=0.5249 (P@1%=0.808), making it the only "honest" baseline metric that did not exploit synthetic label separability.
- **Graph Implication**: The Graph Pipeline must specifically test if structural/topological features contain similar synthetic artifacts (e.g., hardcoded degree distributions).

## 4. Hardware Constraints & Software Availability
- **System**: Dell G15.
- **CPU/RAM**: 16 logical cores, 15.69 GB RAM available.
- **Software**: Python 3.13.5. DuckDB, PyArrow, Pandas present.
- **Contradiction/Blocker**: `torch` (PyTorch) and `torch_geometric` are **NOT INSTALLED** on this system. The prompt requires training a GNN (GraphSAGE / GAT), which strictly requires these libraries.

## 5. Architectural Strategy for Phase 3B
- **Out-of-Core Processing**: 75M CDRs cannot fit in 15.7 GB RAM alongside OS and Python overhead. We will continue using DuckDB for graph aggregation and PyArrow/Parquet for edge list storage.
- **Graph Framework**: To handle the graph on limited RAM, we will construct disk-backed edge lists and use PyTorch Geometric's `NeighborLoader` (or custom sampling) for batch-wise GraphSAGE training. Full-batch GNN training is impossible.
- **Temporal Graphs**: Graph construction must support snapshotting or filtering based on event `timestamp` to ensure chronological evaluation without future-edge leakage.

## 6. Conclusion
The dataset is graph-ready, but the environment requires dependencies to be installed (`torch`, `torch_geometric`). Furthermore, given the synthetic separability issue discovered in Phase 3A, the most critical evaluation in Phase 3B will be whether the *structural* graph features suffer from the same generator artifacts as the behavioral features.
