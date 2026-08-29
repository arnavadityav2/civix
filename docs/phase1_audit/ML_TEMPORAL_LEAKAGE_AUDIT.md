# ML TEMPORAL LEAKAGE AUDIT

## 1. ML Training Snapshots
ML models must train on historical states without seeing the future.

## 2. Validation
All graph and SQL extracts for ML training MUST include a `AS_OF_TIMESTAMP` parameter.
Query pattern: `WHERE tx_start <= AS_OF AND tx_end > AS_OF`.
Because all Gate 2 resolutions heavily enforce `tx_start`/`tx_end`, temporal leakage is structurally prevented.

**Verdict**: PASS.\n