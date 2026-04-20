# Telecom Churn ML Application

Production-style churn prediction project with:
- model training + tuning (`train.py`)
- FastAPI serving (`app.py`)
- batch scoring (`batch_predict.py`)
- drift monitoring (`monitor_drift.py`)
- Docker + GitHub Actions workflows

## 1) Prerequisites

- Python 3.10+ (3.11 recommended)
- `pip`
- (Optional) Docker

## 2) Setup

From project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Train model artifacts (first step)

This creates/refreshes:
- `churn_model.pkl`
- `challenger_model.pkl` (if available)
- `imputer.pkl`
- `scaler.pkl`
- `model_config.json`

```bash
python3 train.py --data-path "WA_Fn-UseC_-Telco-Customer-Churn 2.csv"
```

For quick smoke training:

```bash
python3 train.py --data-path "WA_Fn-UseC_-Telco-Customer-Churn 2.csv" --sample-size 400 --skip-mlflow
```

## 4) Run API locally

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

## 5) API usage (endpoint guide)

Base URL (local):

```text
http://localhost:8000
```

### `GET /health`
Returns service health and active model metadata.

Example:

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "healthy",
  "model": "XGBoost",
  "ab_enabled": true,
  "challenger_loaded": true
}
```

### `POST /predict`
Scores one customer record and returns:
- `churn_probability`
- `risk_level`
- `recommended_action`
- `model_version`
- `experiment_group`

Health check:

```bash
curl http://localhost:8000/health
```

Prediction example:

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "customerID": "CUST-1001",
    "tenure": 5,
    "MonthlyCharges": 89.5,
    "TotalCharges": 430.0,
    "Contract": "Month-to-month",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "TechSupport": "No",
    "PaymentMethod": "Electronic check",
    "PaperlessBilling": "Yes",
    "gender": "Male",
    "SeniorCitizen": 0,
    "Partner": "No",
    "Dependents": "No",
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "OnlineBackup": "No",
    "DeviceProtection": "No",
    "StreamingTV": "No",
    "StreamingMovies": "No"
  }'
```

Example response:

```json
{
  "churn_probability": 0.7421,
  "risk_level": "CRITICAL",
  "recommended_action": "Immediate retention call + loyalty offer",
  "model_version": "XGBoost",
  "experiment_group": "CONTROL"
}
```

## 6) Run batch scoring

Input file should include customer columns expected by the feature pipeline.

```bash
python3 batch_predict.py --input-csv active_customers.csv
```

Outputs:
- `predictions_YYYYMMDD.csv`
- `high_risk_customers.csv`

## 7) Run drift monitoring

Compares reference training data vs current production snapshot.

```bash
python3 monitor_drift.py \
  --reference-csv "WA_Fn-UseC_-Telco-Customer-Churn 2.csv" \
  --current-csv active_customers.csv \
  --output-json drift_report.json
```

If `drift_report.json` has `"should_retrain": true`, retrain via `train.py`.

## 8) Run with Docker

Build:

```bash
docker build -t telecom-churn-api:latest .
```

Run:

```bash
docker run --rm -p 8000:8000 telecom-churn-api:latest
```

Then test:

```bash
curl http://localhost:8000/health
```

## 9) A/B model routing in API

`app.py` supports control/challenger routing (deterministic by `customerID` hash).

Environment variables:
- `AB_TEST_ENABLED` (default: `true`)
- `AB_SPLIT_RATIO` (default: `0.2`)
- `CONTROL_MODEL_PATH` (default: `churn_model.pkl`)
- `CHALLENGER_MODEL_PATH` (default: `challenger_model.pkl`)

Example:

```bash
AB_TEST_ENABLED=true AB_SPLIT_RATIO=0.2 uvicorn app:app --reload
```

## 10) GitHub Actions

Included workflows:
- `.github/workflows/ci.yml`  
  Runs syntax checks, training smoke test, and Docker build.
- `.github/workflows/retrain-on-drift.yml`  
  Runs drift detection and retrains only if drift threshold is exceeded.

## 11) Troubleshooting

- **ModuleNotFoundError**: run `pip install -r requirements.txt` in active environment.
- **Missing artifacts on API startup**: run `train.py` first to generate model files.
- **Docker build fails for missing files**: confirm `churn_model.pkl`, `scaler.pkl`, `imputer.pkl`, and `model_config.json` exist in project root.

# data_project

