from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler

from features import prepare_model_frame

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover
    XGBClassifier = None


def best_threshold(y_true: pd.Series, y_proba: np.ndarray) -> tuple[float, float]:
    thresholds = np.linspace(0.05, 0.95, 19)
    best_t, best_f1 = 0.5, -1.0
    for t in thresholds:
        f1 = f1_score(y_true, (y_proba >= t).astype(int))
        if f1 > best_f1:
            best_t, best_f1 = float(t), float(f1)
    return best_t, best_f1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train churn model with tuning + MLflow.")
    parser.add_argument("--data-path", default="WA_Fn-UseC_-Telco-Customer-Churn 2.csv")
    parser.add_argument("--sample-size", type=int, default=0, help="Use N rows for fast smoke runs.")
    parser.add_argument("--tracking-uri", default="sqlite:///mlflow.db")
    parser.add_argument("--experiment", default="telecom-churn")
    parser.add_argument("--model-out", default="churn_model.pkl")
    parser.add_argument("--challenger-out", default="challenger_model.pkl")
    parser.add_argument("--scaler-out", default="scaler.pkl")
    parser.add_argument("--imputer-out", default="imputer.pkl")
    parser.add_argument("--config-out", default="model_config.json")
    parser.add_argument("--skip-mlflow", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    if args.sample_size and args.sample_size > 0:
        df = df.sample(min(args.sample_size, len(df)), random_state=42).reset_index(drop=True)

    X, y = prepare_model_frame(df, training=True)
    if y is None:
        raise ValueError("Target column `Churn` missing from dataset.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    imputer = SimpleImputer(strategy="median")
    X_train_imputed = pd.DataFrame(
        imputer.fit_transform(X_train), columns=X_train.columns, index=X_train.index
    )
    X_test_imputed = pd.DataFrame(
        imputer.transform(X_test), columns=X_test.columns, index=X_test.index
    )

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train_imputed), columns=X_train.columns, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test_imputed), columns=X_test.columns, index=X_test.index
    )

    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)

    candidates: list[tuple[str, object, dict[str, list[object]]]] = [
        (
            "Logistic Regression",
            LogisticRegression(max_iter=2000, random_state=42),
            {
                "C": [0.01, 0.1, 1.0, 10.0],
                "solver": ["liblinear", "lbfgs"],
                "class_weight": [None, "balanced"],
            },
        )
    ]

    if XGBClassifier is not None:
        candidates.append(
            (
                "XGBoost",
                XGBClassifier(
                    random_state=42,
                    eval_metric="logloss",
                    use_label_encoder=False,
                    n_jobs=-1,
                ),
                {
                    "n_estimators": [150, 250, 350],
                    "max_depth": [3, 5, 7],
                    "learning_rate": [0.03, 0.1, 0.2],
                    "subsample": [0.8, 1.0],
                    "colsample_bytree": [0.8, 1.0],
                },
            )
        )

    best_name = None
    best_model = None
    best_cv_auc = -np.inf
    model_runs: list[dict[str, object]] = []

    for model_name, estimator, param_grid in candidates:
        search = RandomizedSearchCV(
            estimator=estimator,
            param_distributions=param_grid,
            n_iter=min(8, int(np.prod([len(v) for v in param_grid.values()]))),
            scoring="roc_auc",
            cv=3,
            random_state=42,
            n_jobs=-1,
            verbose=0,
        )
        search.fit(X_train_res, y_train_res)
        proba = search.best_estimator_.predict_proba(X_test_scaled)[:, 1]
        threshold, f1 = best_threshold(y_test, proba)
        result = {
            "name": model_name,
            "best_estimator": search.best_estimator_,
            "best_params": search.best_params_,
            "cv_auc": float(search.best_score_),
            "test_auc": float(roc_auc_score(y_test, proba)),
            "test_f1": float(f1),
            "test_recall": float(recall_score(y_test, (proba >= threshold).astype(int))),
            "threshold": float(threshold),
        }
        model_runs.append(result)

        if result["cv_auc"] > best_cv_auc:
            best_cv_auc = result["cv_auc"]
            best_name = model_name
            best_model = search.best_estimator_

    if best_model is None or best_name is None:
        raise RuntimeError("No model candidates were trained.")

    # Sort descending by CV AUC; 2nd one becomes challenger if available
    model_runs = sorted(model_runs, key=lambda x: float(x["cv_auc"]), reverse=True)
    winner = model_runs[0]
    challenger = model_runs[1] if len(model_runs) > 1 else None

    # Persist artifacts used by API
    joblib.dump(winner["best_estimator"], args.model_out)
    joblib.dump(imputer, args.imputer_out)
    joblib.dump(scaler, args.scaler_out)
    if challenger:
        joblib.dump(challenger["best_estimator"], args.challenger_out)

    config = {
        "model_name": winner["name"],
        "features": list(X_train.columns),
        "n_features": int(X_train.shape[1]),
        "optimal_threshold": winner["threshold"],
        "training_date": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "roc_auc": winner["test_auc"],
            "f1": winner["test_f1"],
            "recall": winner["test_recall"],
        },
        "ab_test": {
            "enabled": bool(challenger is not None),
            "control_model_file": args.model_out,
            "challenger_model_file": args.challenger_out if challenger else None,
            "control_name": winner["name"],
            "challenger_name": challenger["name"] if challenger else None,
            "split_ratio": 0.2,
        },
    }
    with open(args.config_out, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    if not args.skip_mlflow:
        import mlflow
        import mlflow.sklearn

        mlflow.set_tracking_uri(args.tracking_uri)
        mlflow.set_experiment(args.experiment)
        with mlflow.start_run(run_name=f"train-{winner['name'].replace(' ', '_')}"):
            mlflow.log_param("winner_model", winner["name"])
            mlflow.log_param("n_features", X_train.shape[1])
            mlflow.log_param("train_rows", X_train.shape[0])
            mlflow.log_param("test_rows", X_test.shape[0])
            mlflow.log_param("smote_applied", True)
            for k, v in winner["best_params"].items():
                mlflow.log_param(f"winner_{k}", v)
            mlflow.log_metric("winner_cv_auc", winner["cv_auc"])
            mlflow.log_metric("winner_test_auc", winner["test_auc"])
            mlflow.log_metric("winner_test_f1", winner["test_f1"])
            mlflow.log_metric("winner_test_recall", winner["test_recall"])
            mlflow.log_metric("winner_threshold", winner["threshold"])
            for idx, run in enumerate(model_runs, start=1):
                mlflow.log_metric(f"candidate_{idx}_cv_auc", float(run["cv_auc"]))
                mlflow.log_metric(f"candidate_{idx}_test_auc", float(run["test_auc"]))
            mlflow.log_artifact(args.config_out)
            mlflow.sklearn.log_model(
                sk_model=winner["best_estimator"], artifact_path="model", registered_model_name=None
            )

    print("Training complete.")
    print(f"Winner: {winner['name']}")
    print(f"Test AUC: {winner['test_auc']:.4f}, F1: {winner['test_f1']:.4f}")
    if challenger:
        print(f"Challenger saved: {challenger['name']}")


if __name__ == "__main__":
    main()

