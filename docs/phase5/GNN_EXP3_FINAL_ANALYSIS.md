# GNN Experiment 3: Final Analysis & Phase 5 Conclusion

## 1. Executive Summary
Experiment 3 was designed to be the definitive test of whether GraphSAGE could extract predictive signal from the CIVIX V2A graph if the 5M-edge truncation (DropEdge) was removed and the model was granted access to the canonical 63.3M-edge graph via `NeighborLoader` mini-batch sampling.

However, the experiment hit a hard **Stop Condition** during the Pre-Flight Memory Smoke Test. PyTorch Geometric (`NeighborLoader`) suffered a critical C++ bindings failure (`'NeighborSampler' requires either 'pyg-lib' or 'torch-sparse'`). Because compiling these sparse-matrix sampling libraries in a CPU-bound Windows environment requires invasive environmental rewrites, the protocol mandates terminating the experiment.

Consequently, **GraphSAGE Experiment 3 could not be executed.** Our final understanding of Graph Neural Networks for this dataset is restricted to the findings of Experiments 1 and 2.

## 2. Experimental Evolution Matrix

| Model | Graph Representation | PR-AUC | ROC-AUC | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **GraphSAGE Exp 1** | 5M edges, raw | 0.1019 | 0.5000 | Collapsed due to unscaled logits. |
| **GraphSAGE Exp 2** | 5M edges, stabilized | 0.1211 | 0.5577 | Learned weak signal; limited by DropEdge. |
| **GraphSAGE Exp 3** | 63.3M edges, sampling | TBD | TBD | **ABORTED**: `NeighborSampler` env failure. |
| Graph LR | Full-graph topology | 0.1433 | 0.6086 | Operates on 108M-edge pre-computed metrics. |
| Graph RF | Full-graph topology | 0.1507 | 0.6222 | Surpasses GNNs on 5M edges. |
| Behavioral RF | Behavioral only | 0.5225 | 0.8454 | |
| **Behavioral XGBoost**| **Behavioral only** | **0.5726** | **0.8646** | **Unchallenged Best-in-Class** |

## 3. Degree Distribution Findings
Before the PyG failure, the Pre-Flight script successfully executed a strict audit of the 63.3M edge graph connectivity, broken down by entity class. 

**Positive Nodes (Criminals):**
* Min Degree: 192
* Median Degree: 466.0
* Max Degree: 1714
* Fully Isolated: 0.00%

**Negative Nodes (Baselines):**
* Min Degree: 159
* Median Degree: 430.0
* Max Degree: 1868
* Fully Isolated: 0.00%

**Conclusion:** Criminal networks in the CIVIX V2A universe are *highly* connected, displaying even higher median degrees than the baseline population. The weak performance of GNNs in Experiment 2 (and the general difficulty of graph modeling on this dataset) is **not** due to a lack of edges or structural isolation. The connections exist; however, the graph's immense density makes it difficult to extract distinguishing structural patterns without massive receptive fields.

## 4. Hardware & Software Bottlenecks
The central finding of Phase 5 Graph Intelligence is that **Graph Neural Networks are fundamentally incompatible with constrained-hardware deployments.**
1. To fit the GNN in 16GB of RAM without sampling, we had to brutally destroy 92% of the graph (DropEdge to 5M edges), which crippled the network's ability to message-pass.
2. To allow the GNN to view the full graph without overflowing RAM, we attempted Mini-Batch Neighborhood Sampling (Exp 3). This requires highly specialized, hardware-specific C++ extensions (`torch-sparse`) which failed in a standard Windows CPU environment.

Traditional ML (Random Forests and XGBoost) bypasses both of these hurdles entirely by relying on DuckDB to calculate topological features out-of-core during Data Engineering.

## 5. Final Recommendation
GNN experimentation should be officially concluded for Phase 5. The Behavioral XGBoost model provides **4.7x the PR-AUC** of the stabilized GraphSAGE model, requires no C++ sampling extensions, trains in a fraction of the time, and trivially scales to 16GB memory bounds.

**Action:** Accept Behavioral XGBoost as the canonical Production Model and proceed to Final Verification testing.
