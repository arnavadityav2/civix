# GNN Experiment 3: Memory Smoke Test & Failure Report

## Execution Context
* **Graph Size:** 250,000 nodes | 63,370,696 edges
* **Batch Size:** 1024 target nodes
* **Sampling Fanout:** [15, 10]
* **Target Load:** 15 mini-batches

## Pre-Flight Status
1. **Canonical Integrity:** PASSED (63,370,696 edges loaded without alteration).
2. **Split Isolation:** PASSED (0 overlapping entities across TRAIN/VAL/TEST).
3. **Degree Audit:** PASSED (Median degree 466 for positives; no isolated nodes).
4. **Feature Scaling:** PASSED (Standardized on Train nodes only).

## Smoke Test Failure
During the initialization of `NeighborLoader` and the first mini-batch extraction, the environment experienced an unrecoverable PyTorch Geometric failure.

### Error Details
* **Failure Point:** `NeighborLoader` initialization / `NeighborSampler` execution.
* **Error Message:** `Exception: 'NeighborSampler' requires either 'pyg-lib' or 'torch-sparse'`
* **RAM Usage:** ~5.2 GB at failure point (Graph loaded successfully, failed at C++ bindings).
* **Environment Details:** Windows OS / CPU-only execution.

### Root Cause
PyTorch Geometric's `NeighborLoader` relies on compiled C++ extensions (`pyg-lib` and `torch-sparse`) to rapidly extract subgraph neighborhoods from massive CSR/CSC sparse matrices. In this Windows/CPU environment, these compiled extensions are not present or correctly configured, meaning PyG physically cannot execute the mini-batch sampling logic required for the 63.3M-edge graph.

### Stop Condition Triggered
Per the experimental protocol:
> *"If NeighborLoader cannot operate correctly in this Windows/Python environment: STOP and report the exact failure. Do not spend multiple days attempting increasingly invasive environment modifications. The inability to execute the intended sampling architecture is itself a valid experimental finding."*

**CONCLUSION:** We cannot proceed to the 30-epoch training phase (Phase 2). The experiment is terminated at the Smoke Test due to hard environment constraints blocking mini-batch neighborhood sampling.
