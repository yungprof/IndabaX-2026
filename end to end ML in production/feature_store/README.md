# Feature Store Migration (Feast-ready)

This project now centralizes feature logic in `features.py` so training, API, and batch scoring use the same transformations.

## Phase 1 (completed)
- Shared feature engineering in `features.py`
- Aligned feature columns via `model_config.json`
- No duplicate feature code between API and batch scripts

## Phase 2 (next)
1. Install Feast in a dedicated environment.
2. Define an entity: `customer`.
3. Define feature views for:
   - raw profile attributes (`tenure`, `MonthlyCharges`, etc.)
   - engineered churn features (`charge_tenure_ratio`, `vulnerable_segment`, etc.)
4. Materialize offline -> online store.
5. Replace direct pandas engineering in API with Feast online retrieval.
6. Replace training dataset joins with Feast historical retrieval.

## Suggested directory structure
- `feature_store/repo/feature_repo.py`
- `feature_store/repo/feature_store.yaml`
- `feature_store/repo/data_sources.py`
- `feature_store/repo/features.py`

## Why this matters
- Prevents train/serve skew
- Enables point-in-time correct training data
- Improves governance and lineage for model features

