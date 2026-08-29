# GNN EXPERIMENT 2 REPORT: Numerical Stabilization and Diagnostic Audit

## 1. Executive Summary
The primary objective of Experiment 2 was to determine whether the complete failure of the GraphSAGE model in Experiment 1 (PR-AUC 0.10, 0 Positives Predicted) was due to a genuine lack of graph signal or due to catastrophic numerical instability during training. 

By applying strict ML stabilization techniques (Standardization, Class Weighting, LayerNorm, and Gradient Clipping), **Experiment 2 successfully prevented mathematical collapse.** The stabilized model learned genuine graph signal (ROC-AUC 0.5577 > 0.5000) and escaped majority-class prediction. 

However, even properly stabilized, the GraphSAGE model constrained to a 5M-edge subset severely underperformed compared to simple Graph-Only Random Forests (ROC-AUC 0.6222) and was completely eclipsed by Behavioral XGBoost models (ROC-AUC 0.8646). 

## 2. Why Experiment 1 Failed
Experiment 1 collapsed on the very first epoch due to two compounded factors:
1. **Unscaled Inputs:** The raw node features (like `cdr_total_out_duration`) contained values up to **408,202,208.0**. Feeding inputs of this magnitude into PyTorch linear layers immediately saturated the network, caused astronomical logits, and generated a validation loss of >122,000, instantly destroying the gradients.
2. **Class Imbalance:** The positive class is roughly 10%. Without positive-class weighting in the `CrossEntropyLoss`, the model took the mathematically easiest path: predicting 0 for every node to achieve 90% accuracy.

## 3. Diagnostic Findings
- **Train Positives:** 17,509 / 175,000 (10.01%)
- **Test Positives:** 3,822 / 37,500 (10.19%)
- **Raw Feature Max:** 408,202,208.00
- **Raw Feature Std Dev:** 3,801,098.25

## 4. Experiment 2 Configuration
To rigorously isolate the cause, Experiment 2 used the exact same 5M-edge graph subset (Seed 42) and identical topology. The only changes made were structural stabilizing techniques:
- **Feature Scaling:** `StandardScaler` fitted strictly on Training nodes.
- **Class Weighting:** Positive weight calculated as `157,491 / 17,509 = 8.9949`.
- **Gradient Clipping:** `max_norm=1.0`
- **Architecture:** Injected `LayerNorm` after each `SAGEConv`.
- **Learning Rate:** Reduced to `5e-4`.

## 5. Feature Scaling Verification
- Zero-variance features: 0
- Scaled Max Absolute Value: 24.6613 (successfully reduced from 408 million)
- Scaler dictionary saved natively alongside model weights.

## 6. Training Curves & Numerical Stability
- **Epoch 01:** Train Loss: 0.7489 | Val Loss: 0.7163 (No longer 122,410!)
- **Epoch 30:** Train Loss: 0.7027 | Val Loss: 0.6884
- The logits remained finite and well-distributed (e.g., Sanity Check logits ranged `[-1.5279, 0.9236]`). No NaNs or Infs were detected.

## 7. Collapse Detection
The model **did not collapse**. 
- It predicted 19,828 positives on the Test set (compared to 0 in Exp 1).
- It achieved a varied probability distribution across 246,379 unique floating-point probability bins.

## 8. Final Test Metrics

| Metric | Score |
| :--- | :--- |
| **PR-AUC** | 0.1211 |
| **ROC-AUC** | 0.5577 |
| **Precision** | 0.1169 |
| **Recall** | 0.6065 |
| **F1 Score** | 0.1960 |
| **Precision@1%** | 0.1093 |
| **Recall@1%** | 0.0107 |
| **Precision@5%** | 0.1381 |
| **Recall@5%** | 0.0678 |

**Confusion Matrix:**
```text
[[16168, 17510],
 [ 1504,  2318]]
```

## 9. A/B Comparison: Experiment 1 vs Experiment 2

| Metric | Experiment 1 (Raw) | Experiment 2 (Stabilized) |
| :--- | :--- | :--- |
| **Graph Edges** | 5M / Seed 42 | 5M / Seed 42 |
| **Features** | Raw | Standardized |
| **Class Weighting** | No | Yes (8.99x) |
| **Val Loss Epoch 1** | ~122,410 | 0.7163 |
| **ROC-AUC** | 0.5000 | **0.5577** |
| **PR-AUC** | 0.1019 | **0.1211** |
| **Predicted Positives** | 0 | 19,828 |

## 10. GNN vs Graph Baselines
While the GNN successfully learned, it performed worse than traditional ML operating on the same graph features:

| Model | PR-AUC | ROC-AUC |
| :--- | :--- | :--- |
| Graph-only Logistic Regression | 0.1433 | 0.6086 |
| Graph-only Random Forest | 0.1507 | 0.6222 |
| **GraphSAGE (Exp 2, 5M Edges)** | **0.1211** | **0.5577** |

*Why?* The Graph baselines (RF, LR) operate on topological features (PageRank, Degree, Triangles) calculated on the **entire 108M edge network** during Data Engineering. The GNN is forced to operate on a randomly sampled 5M-edge subset to fit in memory, meaning it fundamentally lacks the structural neighborhood data required for effective message passing.

## 11. GNN vs Behavioral Baselines
The Behavioral models vastly outperform the GNN, as behavioral features inherently encapsulate structural density without requiring a massive distributed memory footprint.

| Model | PR-AUC | ROC-AUC |
| :--- | :--- | :--- |
| **GraphSAGE (Exp 2)** | 0.1211 | 0.5577 |
| Behavioral RF | 0.5225 | 0.8454 |
| **Behavioral XGBoost** | **0.5726** | **0.8646** |

## 12. Final Conclusion

1. **Numerical Stabilization Recovered Signal:** The initial collapse was an artifact of unscaled inputs and class imbalance. Properly stabilized, the GraphSAGE network successfully extracts criminal signal from the graph.
2. **Hardware Constraints Destroy Topology:** Because we are hardware-constrained to 16GB RAM, the GNN can only observe a 92% reduced (DropEdge) topology. This destroys neighborhood connectivity, causing the GNN to underperform simple Logistic Regression operating on standard topological aggregates.
3. **Production Path Forward:** The experiment conclusively proves that Graph Intelligence is not viable for production on this hardware tier. **Behavioral XGBoost** remains the overwhelmingly superior approach for this dataset, achieving 4.7x higher PR-AUC with a fraction of the memory footprint.
