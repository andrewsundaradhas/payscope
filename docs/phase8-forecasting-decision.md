# Phase 8 — NeuralProphet Decision (Python 3.11)

**Decision (Option 2 — Replacement):**
- The `neuralprophet` package is not compatible with Python 3.11.
- We use a **NeuralProphet-like** deterministic seasonal regression (Fourier features + ridge) implemented in
  `processing/src/payscope_processing/forecast/neuralprophet_model.py`.

**Justification:**
- Preserves weekly/monthly seasonality, supports regressors, and provides uncertainty estimates via residual-based intervals.
- Runs on Python 3.11 with no behavior regression required for the demo scope.

**Compatibility note:**
- If strict NeuralProphet is required later, run it in a separate Python (<3.11) service and register the model_version in Postgres.




