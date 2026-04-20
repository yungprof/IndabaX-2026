
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, json, pandas as pd, numpy as np

model = joblib.load("churn_model.pkl")
scaler = joblib.load("scaler.pkl")
with open("model_config.json") as f:
    config = json.load(f)

app = FastAPI(title="Telecom Churn Prediction API", version="1.0.0")

class CustomerInput(BaseModel):
    tenure: int
    MonthlyCharges: float
    TotalCharges: float
    Contract: str          # "Month-to-month", "One year", "Two year"
    InternetService: str   # "DSL", "Fiber optic", "No"
    OnlineSecurity: str    # "Yes", "No", "No internet service"
    TechSupport: str       # "Yes", "No", "No internet service"
    PaymentMethod: str
    PaperlessBilling: str  # "Yes", "No"
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str

class PredictionOutput(BaseModel):
    churn_probability: float
    risk_level: str
    recommended_action: str
    model_version: str

@app.get("/health")
def health():
    return {"status": "healthy", "model": config["model_name"]}

@app.post("/predict", response_model=PredictionOutput)
def predict(customer: CustomerInput):
    try:
        data = customer.dict()
        # Engineer features
        data["charge_tenure_ratio"] = data["MonthlyCharges"] / (data["tenure"] + 1)
        data["avg_monthly_charge"] = data["TotalCharges"] / (data["tenure"] + 1)
        data["charge_increase"] = data["MonthlyCharges"] - data["avg_monthly_charge"]
        data["services_count"] = sum(1 for s in [data["OnlineSecurity"], data["TechSupport"]] if s == "Yes")
        data["has_protection"] = int(data["OnlineSecurity"] == "Yes")
        data["has_support"] = int(data["TechSupport"] == "Yes")
        data["is_new_customer"] = int(data["tenure"] <= 6)
        data["is_high_value"] = int(data["MonthlyCharges"] > 70)
        data["has_streaming"] = 0
        data["vulnerable_segment"] = int(
            data["is_new_customer"] and data["Contract"] == "Month-to-month"
            and not data["has_support"]
        )
        df = pd.DataFrame([data])
        df = pd.get_dummies(df)
        for col in config["features"]:
            if col not in df.columns:
                df[col] = 0
        df = df[config["features"]]
        df_scaled = scaler.transform(df)
        proba = float(model.predict_proba(df_scaled)[0, 1])
        threshold = config["optimal_threshold"]
        if proba > 0.6:
            risk, action = "CRITICAL", "Immediate retention call + loyalty offer"
        elif proba > threshold:
            risk, action = "HIGH", "Trigger automated retention campaign"
        elif proba > 0.2:
            risk, action = "MEDIUM", "Add to watch list, send survey"
        else:
            risk, action = "LOW", "Standard engagement"
        return PredictionOutput(
            churn_probability=round(proba, 4),
            risk_level=risk,
            recommended_action=action,
            model_version=config["model_name"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
