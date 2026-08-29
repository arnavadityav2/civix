# Phase 5 Final Closure

## Executive Summary
Phase 5 established the baseline production viability of the CIVIX ML pipeline by selecting and validating a canonical behavioral model, conducting rigorous cross-universe generalization testing on unseen synthetic datasets, and performing a deep-dive audit into the model's adversarial robustness. The phase concludes with the freezing of the production candidate and the preservation of the Graph Neural Network (GNN) research branch for future exploration.

## Production Model
The canonical prototype model is the **Behavioral XGBoost** (`behavioral_xgboost_20260829T202007`). It was selected because it successfully operates out-of-core, requires no heavy GNN dependencies, and relies strictly on the 60 reconstructed behavioral features. Graph topology was explicitly EXCLUDED from this model to ensure production safety and inference speed.

## Model Performance
### V2A Baseline (Original Test Split = N 37,500)
- **ROC-AUC:** 0.8646
- **PR-AUC:** 0.5726

### V2B Unseen Universe (Full Population: 50,000)
- **Positive Prevalence:** 10.17%
- **ROC-AUC:** 0.8492 [95% CI: 0.8431 – 0.8552]
- **PR-AUC:** 0.5531 [95% CI: 0.5385 – 0.5670]
- **F1-Score:** 0.4953
- **Precision:** 0.4054
- **Recall:** 0.6367
- **Precision @ 1%:** 0.9380 [95% CI: 0.9120 – 0.9600]
- **Recall @ 1%:** 0.0922
- **Precision @ 5%:** 0.7216 [95% CI: 0.7020 – 0.7412]
- **Recall @ 5%:** 0.3545

### V2C Unseen Universe (Full Population: 50,000)
- **Positive Prevalence:** 10.06%
- **ROC-AUC:** 0.8523 [95% CI: 0.8463 – 0.8580]
- **PR-AUC:** 0.5551 [95% CI: 0.5413 – 0.5693]
- **F1-Score:** 0.4994
- **Precision:** 0.4087
- **Recall:** 0.6418
- **Precision @ 1%:** 0.9220 [95% CI: 0.8960 – 0.9460]
- **Recall @ 1%:** 0.0916
- **Precision @ 5%:** 0.7216 [95% CI: 0.7020 – 0.7416]
- **Recall @ 5%:** 0.3586

## Generalization
The evidence supports robustness to parametric distribution shifts generated within the same V2 synthetic data-generating framework. It does NOT establish robustness to real-world CDR/financial data, unseen real-world fraud typologies, different data-generating processes, or adaptive adversaries.

## Distribution Shift
V2B and V2C experienced meaningful parametric shifts relative to V2A, including approximately a ~20% reduction in call activity, ~16–17% reduction in financial volume, and ~31% reduction in spatial diversity. However, these are strictly parametric distribution shifts within the V2 synthetic data-generating framework.

## Hard Negatives
**Robustness Against Synthetic Hard Negatives (Top-1% Budget)**
No verified synthetic hard-negative entities (`scenario_class == 'false_positive'`) entered the Top-1% alert budget in V2B or V2C. These results do not establish robustness against real-world adaptive adversaries or realistic false-positive populations.

**Top-5% Degradation**
However, the penetration rate into the Top-5% budget is materially weaker than the previously diluted estimates suggested:
- **V2B:** 32 / 2,471 = 1.29% (approx. 3.4x higher than the earlier diluted estimate)
- **V2C:** 44 / 2,454 = 1.79% (approx. 4.4x higher than the earlier diluted estimate)

## Statistical Limitations
The original V2A raw test probabilities were NOT preserved. The absence of the original raw V2A predictions prevents retrospective bootstrap comparison of V2A against V2B/V2C. The V2A baseline metrics must be cited only from the preserved canonical model evaluation JSON, and must not be confused with the 175,000-entity V2A training population.

## GNN Investigation
The planned full-topology GraphSAGE experiment could not be executed in the current Windows CPU environment because the required neighborhood-sampling backend was unavailable. Experiment 3 could not execute because the environment lacked pyg-lib or torch-sparse required by NeighborSampler.

The GNN research branch is FROZEN. The canonical 63.3M-edge graph remains untouched. The GNN branch may be revisited later on an appropriate Linux/WSL/cloud/GPU environment.

## Production Boundary
Explicitly, the current evidence does not establish real-world deployment readiness.

## Final Decision
PHASE 5 STATUS: COMPLETE

PRODUCTION MODEL: BEHAVIORAL XGBOOST

GENERALIZATION CLASSIFICATION:
MODERATE CROSS-UNIVERSE GENERALIZATION
WITHIN THE V2 SYNTHETIC FRAMEWORK

GNN STATUS: FROZEN FOR FUTURE REATTEMPT
