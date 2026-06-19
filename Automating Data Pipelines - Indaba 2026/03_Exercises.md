# 03 Exercises

# Ghana Agrivoltaics Pipeline Exercises

These exercises are designed for a 3-hour code-along workshop.

You will build a pipeline around this question:

> Can Ghanaian farms combine solar power generation with crop production without reducing harvest performance?

Dataset:

https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana

Catalog:

https://fair-forward.github.io/datasets/

## Exercise Format

Each module has:

- **Live Task**: do this during the workshop.
- **Checkpoint**: prove the module worked.
- **Stretch**: optional if you move quickly.

By the end, you should produce:

```text
outputs/reports/profile_*.csv
outputs/reports/validation_report.csv
data/processed/crop_performance_summary.csv
data/processed/treatment_comparison.csv
outputs/charts/mean_crop_yield_by_treatment.png
```

## Opening Exercise: Frame The Problem

### Live Task

Write short answers:

1. What decision could this dataset help support?
2. Who might care about the answer?
3. What could go wrong if the data pipeline is wrong?

### Checkpoint

You should be able to explain the problem in one sentence.

Example:

> We are building a pipeline to compare crop performance under agrivoltaic and open-sun conditions in Ghana.

### Stretch

List two extra datasets that would strengthen the analysis.

Examples:

- weather data
- soil data
- crop prices
- installation cost data
- farmer survey data

## Module 1 Exercise: Load Raw Files

### Live Task

Place the downloaded and extracted Kaggle dataset files in:

```text
data/raw/
```

Then list the files:

```python
from pathlib import Path

RAW_DIR = Path("data/raw")

for path in sorted(RAW_DIR.glob("*")):
    print(path.name)
```

Load CSV and Excel files:

```python
import pandas as pd

files = [
    path for path in sorted(RAW_DIR.glob("*"))
    if path.suffix.lower() in [".csv", ".xlsx", ".xls"]
]

tables = {}

for file in files:
    if file.suffix.lower() == ".csv":
        tables[file.stem] = pd.read_csv(file)
    else:
        tables[file.stem] = pd.read_excel(file)

for name, df in tables.items():
    print(name, df.shape)
```

### Checkpoint

You should have:

- at least one raw file listed
- a `tables` dictionary
- printed table names and shapes

### Stretch

Print the memory usage of each loaded table:

```python
for name, df in tables.items():
    memory_mb = df.memory_usage(deep=True).sum() / 1_000_000
    print(name, round(memory_mb, 2), "MB")
```

## Module 2 Exercise: Inspect And Profile

### Live Task

Inspect every table:

```python
for name, df in tables.items():
    print(f"\n{name}")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    display(df.head())
```

Create a profile function:

```python
def profile_table(df):
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[col].dtype) for col in df.columns],
        "missing_count": [int(df[col].isna().sum()) for col in df.columns],
        "missing_pct": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
        "unique_values": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })
```

Save profiles:

```python
REPORTS_DIR = Path("outputs/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

for name, df in tables.items():
    profile = profile_table(df)
    profile.to_csv(REPORTS_DIR / f"profile_{name}.csv", index=False)
    display(profile)
```

### Checkpoint

Answer:

1. Which table looks like crop performance data?
2. Which table looks like energy data?
3. Which columns look like crop, treatment, and yield?
4. Which columns have missing values?

### Stretch

Create a quick missingness summary across all tables:

```python
missing_summary = []

for name, df in tables.items():
    missing_summary.append({
        "table": name,
        "rows": len(df),
        "columns": len(df.columns),
        "total_missing": int(df.isna().sum().sum()),
    })

pd.DataFrame(missing_summary)
```

## Module 3 Exercise: Define The Data Contract

### Live Task

Fill in the raw column names for the fields you can find:

```python
COLUMN_MAP = {
    "plot": "replace_with_raw_column_name",
    "treatment": "replace_with_raw_column_name",
    "crop": "replace_with_raw_column_name",
    "replicate": "replace_with_raw_column_name",
    "date": "replace_with_raw_column_name",
    "yield_value": "replace_with_raw_column_name",
    "yield_unit": "replace_with_raw_column_name",
    "energy_value": "replace_with_raw_column_name",
    "energy_unit": "replace_with_raw_column_name",
}
```

If a field is not present, remove it from the map or leave a note.

Create the rename function:

```python
def clean_column_name(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def rename_with_contract(df, column_map):
    rename_map = {
        raw_column: standard_column
        for standard_column, raw_column in column_map.items()
        if raw_column in df.columns
    }

    renamed = df.rename(columns=rename_map).copy()
    renamed.columns = [clean_column_name(col) for col in renamed.columns]
    return renamed
```

Apply it:

```python
crop_table_name = "replace_with_actual_table_name"
crop_raw = tables[crop_table_name]
crop_renamed = rename_with_contract(crop_raw, COLUMN_MAP)

print(crop_renamed.columns)
```

### Checkpoint

You should have a crop table with standard column names for at least:

- `crop`
- `treatment`
- `yield_value`

### Stretch

Write a short note explaining which fields were ambiguous and how you resolved them.

## Module 4 Exercise: Clean And Standardize

### Live Task

Create cleaning functions:

```python
def clean_text(value):
    if pd.isna(value):
        return value
    return str(value).strip().lower().replace("_", " ")
```

Standardize crop names:

```python
def standardize_crop(value):
    value = clean_text(value)

    crop_map = {
        "tomato": "tomato",
        "tomatoes": "tomato",
        "chilli": "chilli pepper",
        "chili": "chilli pepper",
        "chilli pepper": "chilli pepper",
        "chili pepper": "chilli pepper",
        "egg plant": "eggplant",
        "eggplant": "eggplant",
    }

    return crop_map.get(value, value)
```

Standardize treatment names:

```python
def standardize_treatment(value):
    value = clean_text(value)

    if value in ["control", "open sun", "open-sun", "no pv", "no panels"]:
        return "open_sun_control"

    if value in ["agrivoltaic", "raised pv", "under pv", "under panels", "solar pv"]:
        return "agrivoltaic"

    if value in ["ground mounted pv", "ground-mounted pv", "bare land pv"]:
        return "ground_mounted_pv"

    return value
```

Clean the table:

```python
crop_clean = crop_renamed.copy()

if "crop" in crop_clean.columns:
    crop_clean["crop"] = crop_clean["crop"].apply(standardize_crop)

if "treatment" in crop_clean.columns:
    crop_clean["treatment"] = crop_clean["treatment"].apply(standardize_treatment)

if "date" in crop_clean.columns:
    crop_clean["date"] = pd.to_datetime(crop_clean["date"], errors="coerce")

if "yield_value" in crop_clean.columns:
    crop_clean["yield_value"] = pd.to_numeric(crop_clean["yield_value"], errors="coerce")
```

Inspect cleaned values:

```python
for column in ["crop", "treatment"]:
    if column in crop_clean.columns:
        print(column, sorted(crop_clean[column].dropna().unique()))
```

### Checkpoint

Crop and treatment values should be consistent enough to group by.

### Stretch

Find the raw values that changed after standardization.

## Module 5 Exercise: Validate

### Live Task

Run validation checks:

```python
ALLOWED_CROPS = {"tomato", "chilli pepper", "eggplant"}
ALLOWED_TREATMENTS = {"open_sun_control", "agrivoltaic", "ground_mounted_pv"}

errors = []

required_columns = ["crop", "treatment", "yield_value"]
missing = [column for column in required_columns if column not in crop_clean.columns]
if missing:
    errors.append(f"Missing required columns: {missing}")

if "crop" in crop_clean.columns:
    invalid_crops = sorted(set(crop_clean["crop"].dropna()) - ALLOWED_CROPS)
    if invalid_crops:
        errors.append(f"Unexpected crop values: {invalid_crops}")

if "treatment" in crop_clean.columns:
    invalid_treatments = sorted(set(crop_clean["treatment"].dropna()) - ALLOWED_TREATMENTS)
    if invalid_treatments:
        errors.append(f"Unexpected treatment values: {invalid_treatments}")

if "yield_value" in crop_clean.columns and (crop_clean["yield_value"] < 0).any():
    errors.append("yield_value contains negative values")
```

Save a validation report:

```python
validation_report = pd.DataFrame({
    "status": ["error"] * len(errors) if errors else ["ok"],
    "message": errors if errors else ["Validation passed"],
})

validation_report.to_csv(REPORTS_DIR / "validation_report.csv", index=False)
validation_report
```

### Checkpoint

You should have:

```text
outputs/reports/validation_report.csv
```

### Stretch

Add one more validation rule:

- duplicate check
- missing yield check
- invalid date check
- unexpected plot check

## Module 6 Exercise: Transform And Visualize

### Live Task

Create crop summary:

```python
crop_summary = (
    crop_clean
    .dropna(subset=["crop", "treatment", "yield_value"])
    .groupby(["crop", "treatment"], dropna=False)
    .agg(
        observations=("yield_value", "count"),
        mean_yield=("yield_value", "mean"),
        median_yield=("yield_value", "median"),
        min_yield=("yield_value", "min"),
        max_yield=("yield_value", "max"),
    )
    .reset_index()
)

crop_summary
```

Create treatment comparison:

```python
treatment_comparison = (
    crop_summary
    .pivot(index="crop", columns="treatment", values="mean_yield")
    .reset_index()
)

if {"agrivoltaic", "open_sun_control"}.issubset(treatment_comparison.columns):
    treatment_comparison["yield_difference"] = (
        treatment_comparison["agrivoltaic"] - treatment_comparison["open_sun_control"]
    )
    treatment_comparison["yield_difference_pct"] = (
        treatment_comparison["yield_difference"] / treatment_comparison["open_sun_control"] * 100
    ).round(2)

treatment_comparison
```

Save outputs:

```python
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

crop_summary.to_csv(PROCESSED_DIR / "crop_performance_summary.csv", index=False)
treatment_comparison.to_csv(PROCESSED_DIR / "treatment_comparison.csv", index=False)
```

Create chart:

```python
import matplotlib.pyplot as plt
import seaborn as sns

CHARTS_DIR = Path("outputs/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

plt.figure(figsize=(10, 6))
sns.barplot(data=crop_summary, x="crop", y="mean_yield", hue="treatment")
plt.title("Mean Crop Yield by Treatment")
plt.xlabel("Crop")
plt.ylabel("Mean yield")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "mean_crop_yield_by_treatment.png", dpi=150)
plt.close()
```

### Checkpoint

You should have:

```text
data/processed/crop_performance_summary.csv
data/processed/treatment_comparison.csv
outputs/charts/mean_crop_yield_by_treatment.png
```

### Stretch

Create a second chart for `yield_difference_pct`.

## Closing Exercise: Responsible Interpretation

Write 5-7 sentences:

1. What does the processed data suggest?
2. Which crop appears most promising under agrivoltaic conditions?
3. What limitations should be communicated?
4. What extra data would strengthen the analysis?
5. What should we avoid claiming?

Use careful language. This is a pilot dataset, not a universal answer for all Ghanaian farms.

## Final Checklist

Before leaving, confirm that you created:

- [ ] raw files in `data/raw/`
- [ ] profile reports in `outputs/reports/`
- [ ] validation report in `outputs/reports/`
- [ ] crop summary in `data/processed/`
- [ ] treatment comparison in `data/processed/`
- [ ] chart in `outputs/charts/`
- [ ] short written interpretation

