from pathlib import Path

import pandas as pd


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
) -> list[str]:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        return [f"Missing required columns: {missing}"]
    return []


def validate_allowed_values(
    df: pd.DataFrame,
    column: str,
    allowed_values: set[str],
) -> list[str]:
    if column not in df.columns:
        return []

    actual_values = set(df[column].dropna().astype(str))
    invalid_values = sorted(actual_values - allowed_values)

    if invalid_values:
        return [f"Unexpected values in {column}: {invalid_values}"]

    return []


def validate_non_negative(
    df: pd.DataFrame,
    columns: list[str],
) -> list[str]:
    errors = []

    for column in columns:
        if column in df.columns and (df[column] < 0).any():
            errors.append(f"{column} contains negative values")

    return errors


def validate_not_missing(
    df: pd.DataFrame,
    columns: list[str],
) -> list[str]:
    errors = []

    for column in columns:
        if column in df.columns and df[column].isna().any():
            count = int(df[column].isna().sum())
            errors.append(f"{column} contains {count} missing values")

    return errors


def build_validation_report(errors: list[str]) -> pd.DataFrame:
    if not errors:
        return pd.DataFrame([{"status": "ok", "message": "Validation passed"}])

    return pd.DataFrame(
        {"status": "error", "message": message}
        for message in errors
    )


def save_validation_report(
    report: pd.DataFrame,
    reports_dir: str | Path,
    filename: str = "validation_report.csv",
) -> None:
    output_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_dir / filename, index=False)
