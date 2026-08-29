# CIVIX 2.0

## Overview
CIVIX 2.0 is an advanced machine learning pipeline and platform designed for large-scale behavioral classification. It processes complex Call Detail Records (CDRs) and transactional data to extract robust behavioral and graph-topological features. 

## Repository Structure
This repository contains the complete ML source code and experiment provenance:
* `civix_ml/`: Core feature engineering, model definitions, and inference logic.
* `civix_generator/`: The synthetic V2 data generator.
* `docs/`: Phase 1-5 architectural decisions, schema registries, and rigorous ML audit reports.
* `scratch/`: Historical diagnostic scripts used for data reconciliation and metric auditing.
* `scripts/`: Helper scripts for orchestration.
* `models/metadata/`: Preserved JSON configuration/metric files for all historical ML experiments.

## Canonical Production Model
Phase 5 evaluation concluded with the selection of the **Behavioral XGBoost** (`behavioral_xgboost_20260829T202007`) as the canonical prototype model. 

It was selected because it successfully operates out-of-core without heavy GNN dependencies, relying strictly on the **60 reconstructed behavioral features**. Graph topology was explicitly excluded from the final production model to prioritize inference speed and scalability.

### Phase 5 Conclusion
Rigorous multi-universe testing across V2A, V2B, and V2C established **moderate cross-universe generalization within the V2 synthetic framework**. 

*Important Reproducibility Caveats:*
* The current evidence relies entirely on synthetic evaluation. It does NOT establish real-world deployment readiness, nor does it guarantee survival against unseen real-world fraud typologies or adaptive adversaries.
* The original V2A raw test prediction scores were not preserved during Phase 2/3. Consequently, V2A metrics are cited from historical logs, and bootstrapping could not be performed for V2A.

## GNN Research Branch
The Graph Neural Network (GNN) and GraphSAGE research branch is currently **FROZEN FOR FUTURE REATTEMPT**. 

Experiments 1 and 2 successfully built PyG artifacts, but the planned full-topology GraphSAGE execution (Experiment 3) could not be completed on the current Windows CPU environment. The required neighborhood-sampling backend components (`pyg-lib` and `torch-sparse`) were unavailable. Future reattempts should utilize a Linux/WSL/cloud/GPU-capable environment. The canonical 63.3M-edge graph remains safely preserved and unchanged.

## External Data & Artifact Limitations
Git is optimized for code and documentation. Large generated datasets and binary model artifacts are **NOT** committed to this repository.

To recreate the development environment, teammates must obtain the following artifacts externally (typically stored in a shared network drive mapped to `D:\`):
* `D:\civix_data\synthetic\`: Contains `profile_v2_v2a`, `profile_v2_v2b`, and `profile_v2_v2c` (Parquet files and the 63.3M edge graph).
* `D:\civix_data\models\`: Contains the actual serialized model binaries (`*.pkl`, `*.joblib`, `*.pt`).
* `D:\civix_data\models\predictions\`: Contains the `v2b_predictions.parquet` and `v2c_predictions.parquet` files.

If you mount your external data to a different path, update `civix_ml/config.py` accordingly.

## Installation and Execution
1. **Environment Setup:** `pip install -r requirements.txt` (Note: PyTorch and PyG are excluded from the core requirements to enforce the GNN-independent production boundary).
2. **Feature Pipeline:** `python -m civix_ml.features.pipeline`
3. **Inference Execution:** `python -m civix_ml.inference.run`
4. **Experiment Tracking:** Review the JSON metadata in `models/metadata/` to inspect historical model hyperparameters and metrics.
