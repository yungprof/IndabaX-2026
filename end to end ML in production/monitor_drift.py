from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from features import prepare_model_frame


def categorical_drift_score(ref: pd.Series, cur: pd.Series) -> float:
    ref_dist = ref.astype(str).value_counts(normalize=True)
    cur_dist = cur.astype(str).value_counts(normalize=True)
    categories = sorted(set(ref_dist.index).union(set(cur_dist.index)))
    ref_aligned = np.array([ref_dist.get(c, 0.0) for c in categories], dtype=float)
    cur_aligned = np.array([cur_dist.get(c, 0.0) for c in categories], dtype=float)
    return float(np.abs(ref_aligned - cur_aligned).sum() / 2.0)  # total variation distance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple data drift monitor.")
    parser.add_argument("--reference-csv", default="WA_Fn-UseC_-Telco-Customer-Churn 2.csv")
    parser.add_argument("--current-csv", default="active_customers.csv")
    parser.add_argument("--output-json", default="drift_report.json")
    parser.add_argument("--drift-threshold", type=float, default=0.25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ref_path = Path(args.reference_csv)
    cur_path = Path(args.current_csv)

    if not ref_path.exists():
        raise FileNotFoundError(f"Reference dataset not found: {ref_path}")
    if not cur_path.exists():
        report = {
            "status": "skipped",
            "reason": f"Current dataset missing: {cur_path}",
            "overall_drift_ratio": 0.0,
            "should_retrain": False,
            "drifted_features": [],
        }
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))
        return

    ref_df = pd.read_csv(ref_path)
    cur_df = pd.read_csv(cur_path)

    # Use same feature prep logic to compare model-facing feature drift
    ref_X, _ = prepare_model_frame(ref_df, training=True)
    cur_X, _ = prepare_model_frame(cur_df, training=False, feature_columns=ref_X.columns)

    drifted = []
    details: dict[str, dict[str, float | str]] = {}

    for col in ref_X.columns:
        ref_col = ref_X[col]
        cur_col = cur_X[col]
        if pd.api.types.is_numeric_dtype(ref_col):
            stat, pvalue = ks_2samp(ref_col.fillna(0), cur_col.fillna(0))
            is_drifted = pvalue < 0.05
            details[col] = {
                "type": "numeric",
                "ks_stat": float(stat),
                "pvalue": float(pvalue),
                "drifted": bool(is_drifted),
            }
        else:
            tvd = categorical_drift_score(ref_col, cur_col)
            is_drifted = tvd > 0.1
            details[col] = {
                "type": "categorical",
                "tvd": float(tvd),
                "drifted": bool(is_drifted),
            }
        if is_drifted:
            drifted.append(col)

    overall_ratio = len(drifted) / max(1, len(ref_X.columns))
    should_retrain = overall_ratio >= args.drift_threshold
    report = {
        "status": "ok",
        "reference_rows": int(len(ref_X)),
        "current_rows": int(len(cur_X)),
        "feature_count": int(ref_X.shape[1]),
        "drifted_features": drifted,
        "overall_drift_ratio": float(overall_ratio),
        "drift_threshold": float(args.drift_threshold),
        "should_retrain": bool(should_retrain),
        "details": details,
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

