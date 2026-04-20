from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


TARGET_COLUMN = "Churn"


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def clean_telco_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning for Telco churn data."""
    cleaned = df.copy()
    if "TotalCharges" in cleaned.columns:
        cleaned["TotalCharges"] = _to_numeric(cleaned["TotalCharges"])
    if "tenure" in cleaned.columns:
        cleaned["tenure"] = _to_numeric(cleaned["tenure"])
    if "MonthlyCharges" in cleaned.columns:
        cleaned["MonthlyCharges"] = _to_numeric(cleaned["MonthlyCharges"])
    if "SeniorCitizen" in cleaned.columns:
        cleaned["SeniorCitizen"] = _to_numeric(cleaned["SeniorCitizen"]).fillna(0).astype(int)
    return cleaned


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    engineered = df.copy()
    tenure = engineered.get("tenure", pd.Series(0, index=engineered.index)).fillna(0)
    monthly = engineered.get("MonthlyCharges", pd.Series(0.0, index=engineered.index)).fillna(0.0)
    total = engineered.get("TotalCharges", pd.Series(0.0, index=engineered.index)).fillna(0.0)

    safe_tenure = tenure + 1
    engineered["charge_tenure_ratio"] = monthly / safe_tenure
    engineered["avg_monthly_charge"] = total / safe_tenure
    engineered["charge_increase"] = monthly - engineered["avg_monthly_charge"]

    service_cols = [c for c in ["OnlineSecurity", "TechSupport"] if c in engineered.columns]
    if service_cols:
        engineered["services_count"] = (engineered[service_cols] == "Yes").sum(axis=1)
    else:
        engineered["services_count"] = 0

    engineered["has_protection"] = (engineered.get("OnlineSecurity", "No") == "Yes").astype(int)
    engineered["has_support"] = (engineered.get("TechSupport", "No") == "Yes").astype(int)
    engineered["is_new_customer"] = (tenure <= 6).astype(int)
    engineered["is_high_value"] = (monthly > 70).astype(int)

    streaming_cols = [c for c in ["StreamingTV", "StreamingMovies"] if c in engineered.columns]
    if streaming_cols:
        engineered["has_streaming"] = (engineered[streaming_cols] == "Yes").any(axis=1).astype(int)
    else:
        engineered["has_streaming"] = 0

    contract = engineered.get("Contract", pd.Series("", index=engineered.index))
    engineered["vulnerable_segment"] = (
        (engineered["is_new_customer"] == 1)
        & (contract == "Month-to-month")
        & (engineered["has_support"] == 0)
    ).astype(int)
    return engineered


def prepare_model_frame(
    df: pd.DataFrame,
    *,
    training: bool,
    feature_columns: Iterable[str] | None = None,
    drop_first: bool = True,
) -> tuple[pd.DataFrame, pd.Series | None]:
    """
    Prepare one-hot encoded feature matrix.
    - training=True: infers feature columns and returns y if TARGET_COLUMN exists
    - training=False: aligns to provided feature_columns
    """
    prepared = clean_telco_dataframe(df)
    prepared = add_engineered_features(prepared)

    y = None
    if TARGET_COLUMN in prepared.columns:
        if prepared[TARGET_COLUMN].dtype == "object":
            y = (prepared[TARGET_COLUMN] == "Yes").astype(int)
        else:
            y = _to_numeric(prepared[TARGET_COLUMN]).fillna(0).astype(int)
        prepared = prepared.drop(columns=[TARGET_COLUMN])

    drop_cols = [c for c in ["customerID", "tenure_bucket"] if c in prepared.columns]
    if drop_cols:
        prepared = prepared.drop(columns=drop_cols)

    cat_cols = prepared.select_dtypes(include=["object", "category"]).columns.tolist()
    encoded = pd.get_dummies(prepared, columns=cat_cols, drop_first=drop_first)

    for col in encoded.columns:
        encoded[col] = _to_numeric(encoded[col]).fillna(0.0)

    if training:
        return encoded, y

    if feature_columns is None:
        raise ValueError("feature_columns must be provided for inference alignment.")

    feature_columns = list(feature_columns)
    for col in feature_columns:
        if col not in encoded.columns:
            encoded[col] = 0.0
    encoded = encoded[feature_columns]
    return encoded, y

