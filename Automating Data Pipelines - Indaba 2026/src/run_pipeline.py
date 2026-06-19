from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from ingest import load_raw_tables
from profile_data import profile_tables, save_profiles
from transform import (
    clean_pipeline_table,
    compare_treatments,
    rename_with_contract,
    summarize_crop_performance,
)
from validate_data import (
    build_validation_report,
    save_validation_report,
    validate_allowed_values,
    validate_non_negative,
    validate_required_columns,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "outputs" / "reports"
CHARTS_DIR = ROOT / "outputs" / "charts"

ALLOWED_CROPS = {"tomato", "chilli pepper", "eggplant"}
ALLOWED_TREATMENTS = {"open_sun_control", "agrivoltaic", "ground_mounted_pv"}

# Update these after inspecting the real dataset files.
CROP_TABLE_NAME = "replace_with_actual_table_name"
COLUMN_MAP = {
    "plot": "replace_with_raw_column_name",
    "treatment": "replace_with_raw_column_name",
    "crop": "replace_with_raw_column_name",
    "replicate": "replace_with_raw_column_name",
    "date": "replace_with_raw_column_name",
    "yield_value": "replace_with_raw_column_name",
    "yield_unit": "replace_with_raw_column_name",
}


def ensure_output_dirs() -> None:
    for directory in [PROCESSED_DIR, REPORTS_DIR, CHARTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def validate_crop_table(crop_df):
    errors = []
    errors.extend(validate_required_columns(crop_df, ["crop", "treatment", "yield_value"]))
    errors.extend(validate_allowed_values(crop_df, "crop", ALLOWED_CROPS))
    errors.extend(validate_allowed_values(crop_df, "treatment", ALLOWED_TREATMENTS))
    errors.extend(validate_non_negative(crop_df, ["yield_value"]))
    return errors


def save_charts(crop_summary, treatment_comparison) -> None:
    plt.figure(figsize=(10, 6))
    sns.barplot(data=crop_summary, x="crop", y="mean_yield", hue="treatment")
    plt.title("Mean Crop Yield by Treatment")
    plt.xlabel("Crop")
    plt.ylabel("Mean yield")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "mean_crop_yield_by_treatment.png", dpi=150)
    plt.close()

    if "yield_difference_pct" in treatment_comparison.columns:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=treatment_comparison, x="crop", y="yield_difference_pct")
        plt.axhline(0, color="black", linewidth=1)
        plt.title("Agrivoltaic Yield Difference Compared With Open-Sun Control")
        plt.xlabel("Crop")
        plt.ylabel("Yield difference (%)")
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / "agrivoltaic_yield_difference_pct.png", dpi=150)
        plt.close()


def main() -> None:
    print("Starting Ghana agrivoltaics pipeline")
    ensure_output_dirs()

    tables = load_raw_tables(RAW_DIR)
    if not tables:
        raise RuntimeError(f"No CSV or Excel files found in {RAW_DIR}")

    profiles = profile_tables(tables)
    save_profiles(profiles, REPORTS_DIR)
    print(f"Profiled {len(profiles)} table(s)")

    if CROP_TABLE_NAME not in tables:
        available = ", ".join(tables.keys())
        raise RuntimeError(
            "Update CROP_TABLE_NAME in src/run_pipeline.py. "
            f"Available tables: {available}"
        )

    crop_renamed = rename_with_contract(tables[CROP_TABLE_NAME], COLUMN_MAP)
    crop_clean = clean_pipeline_table(crop_renamed)

    errors = validate_crop_table(crop_clean)
    validation_report = build_validation_report(errors)
    save_validation_report(validation_report, REPORTS_DIR)

    if errors:
        raise RuntimeError(
            "Validation failed. See outputs/reports/validation_report.csv"
        )

    crop_summary = summarize_crop_performance(crop_clean)
    treatment_comparison = compare_treatments(crop_summary)

    crop_summary.to_csv(PROCESSED_DIR / "crop_performance_summary.csv", index=False)
    treatment_comparison.to_csv(
        PROCESSED_DIR / "treatment_comparison.csv",
        index=False,
    )

    save_charts(crop_summary, treatment_comparison)
    print("Pipeline completed successfully")


if __name__ == "__main__":
    main()
