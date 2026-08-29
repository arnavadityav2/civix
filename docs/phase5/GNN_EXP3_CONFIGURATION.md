# GraphSAGE Experiment 3: Pre-Registered Configuration

## Canonical State
* **Experiment:** GraphSAGE Experiment 3 (Full-Topology Mini-Batch Neighbor Sampling)
* **Dataset:** CIVIX Synthetic World V2A
* **Nodes:** 250,000
* **Canonical edges:** ~63.3M

## Architecture & Hardware
* **Device:** CPU
* **Architecture:** SAGEConv -> LayerNorm -> ReLU -> Dropout -> SAGEConv -> LayerNorm -> Classifier
* **Hidden channels:** 64
* **Layers:** 2
* **Neighbor fanout:** [15,10]

## Training Hyperparameters
* **Epochs:** 30 maximum
* **Seed:** 42
* **Feature scaling:** StandardScaler (Fitted on TRAIN nodes only)
* **Class weighting:** enabled (Calculated from TRAIN labels only)
* **Gradient clipping:** 1.0
* **LayerNorm:** enabled
* **Learning rate:** 5e-4
