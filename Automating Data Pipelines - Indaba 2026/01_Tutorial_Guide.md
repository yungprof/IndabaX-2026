# 01 Tutorial Guide

# Automating a Ghana Agrivoltaics Data Pipeline

## Workshop Style

This is a 3-hour code-along tutorial. We are going to build the pipeline in stages, inspect what breaks, fix it, and end with real outputs.

The goal is not to memorize pandas. The goal is to learn the working rhythm of a data engineer:

```text
look at the raw data
make assumptions explicit
clean carefully
validate before trusting
transform into useful outputs
communicate limits honestly
```

Raw data often looks calm until you ask it one serious question. So we will not start with charts. We will start by inspecting the files.

## The Problem

**Can Ghanaian farms combine solar power generation with crop production without reducing harvest performance?**

We will use a Ghana agrivoltaics dataset from the FAIR Forward Open Data and Use Cases catalog. Agrivoltaics means using the same land for crop production and solar energy generation, usually by placing raised solar PV panels above crops.

The practical question is simple:

> Do crops under raised solar panels perform differently from crops grown in open sun?

The pipeline question is just as important:

> Can we turn raw field data into trusted outputs without doing manual spreadsheet magic every time?

## Dataset

- FAIR Forward catalog: https://fair-forward.github.io/datasets/
- Kaggle dataset: https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
- Country: Ghana
- Provider: Responsible AI Lab, KNUST
- License: CC-BY 4.0
- Data type: Tabular
- Crops: tomatoes, chilli pepper, and eggplant

The dataset compares:

- open-sun control farming
- agrivoltaic farming with raised solar panels
- traditional ground-mounted solar PV on bare land

## 3-Hour Workshop Flow

| Time | Module | What We Build |
| --- | --- | --- |
| 0:00-0:15 | Opening | Problem, dataset, project shape |
| 0:15-0:35 | Module 1 | Set up the workspace and load raw files |
| 0:35-1:05 | Module 2 | Inspect and profile the data |
| 1:05-1:30 | Module 3 | Define the data contract |
| 1:30-1:40 | Break | Quick reset |
| 1:40-2:05 | Module 4 | Clean crop, treatment, date, and numeric fields |
| 2:05-2:30 | Module 5 | Validate the cleaned data |
| 2:30-2:50 | Module 6 | Transform data into crop insights |
| 2:50-3:00 | Wrap | Save outputs, discuss responsible use |

Each module follows this pattern:

```text
Big idea
Instructor demo
Your turn
Checkpoint
Recap
```

## Project Structure

Use this structure:

```text
Automating Data Pipelines - Indaba 2026/
  README.md
  01_Tutorial_Guide.md
  02_Facilitator_Guide.md
  03_Exercises.md
  requirements.txt
  data/
    raw/
    processed/
  notebooks/
  src/
  outputs/
    charts/
    reports/
```

Rule of thumb:

- `data/raw/` is where untouched source files live.
- `data/processed/` is where pipeline-generated outputs live.
- `outputs/reports/` is where diagnostics live.
- `outputs/charts/` is where visual outputs live.
- `src/` is where reusable pipeline code goes.

Do not manually edit raw files. If raw data needs fixing, write code that fixes it.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Download the dataset from Kaggle:

```bash
kaggle datasets download responsibleailab/agrivoltaic-dataset-ghana -p data/raw --unzip
```

Manual fallback:

1. Visit https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
2. Download the ZIP file.
3. Extract the files.
4. Place them in `data/raw/`.

## Module 1: Load Raw Files

### Big Idea

Before building a pipeline, prove that your code can find the raw data. A pipeline that cannot locate its inputs is not a pipeline. It is a motivational poster.

### Instructor Demo

Create the basic paths:

```python
from pathlib import Path

ROOT = Path(".")
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "outputs" / "reports"
CHARTS_DIR = ROOT / "outputs" / "charts"

for directory in [RAW_DIR, PROCESSED_DIR, REPORTS_DIR, CHARTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
```

List the raw files:

```python
raw_files = sorted(RAW_DIR.glob("*"))

for path in raw_files:
    print(path.name)
```

Load supported tabular files:

```python
import pandas as pd

tabular_files = [
    path for path in raw_files
    if path.suffix.lower() in [".csv", ".xlsx", ".xls"]
]

tables = {}

for file in tabular_files:
    if file.suffix.lower() == ".csv":
        tables[file.stem] = pd.read_csv(file)
    else:
        tables[file.stem] = pd.read_excel(file)

for name, df in tables.items():
    print(name, df.shape)
```

### Your Turn

Run the code and answer:

- How many files did you load?
- Which files are CSV?
- Which files are Excel?
- Which table looks like crop data?
- Which table looks like energy data?

### Checkpoint

You should have a `tables` dictionary where each key is a table name and each value is a pandas DataFrame.

### Recap

We did not clean anything yet. That is deliberate. First we locate, load, and name the inputs.

## Module 2: Inspect And Profile The Data

### Big Idea

Inspection is where you earn the right to transform. If you skip this step, every later chart is built on vibes.

### Instructor Demo

Look at table previews:

```python
for name, df in tables.items():
    print(f"\n{name}")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    display(df.head())
```

Create a profiling helper:

```python
def profile_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[col].dtype) for col in df.columns],
        "missing_count": [int(df[col].isna().sum()) for col in df.columns],
        "missing_pct": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
        "unique_values": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })
```

Profile every table:

```python
profiles = {
    name: profile_table(df)
    for name, df in tables.items()
}

for name, profile in profiles.items():
    print(f"\n{name}")
    display(profile)
```

Save reports:

```python
for name, profile in profiles.items():
    profile.to_csv(REPORTS_DIR / f"profile_{name}.csv", index=False)
```

### Your Turn

Find:

- the table that contains crop performance
- columns that look like crop labels
- columns that look like treatment or plot labels
- columns that look like yield or measurement values
- missing values that could affect analysis

### Checkpoint

You should have profile CSV files in:

```text
outputs/reports/
```

### Recap

Profiling tells us what the dataset actually contains. A data pipeline should react to reality, not to what we hoped the CSV would look like.

## Module 3: Define The Data Contract

### Big Idea

A data contract is a small agreement between the raw source and your pipeline. It says: these are the fields we need, and these are the names our pipeline will use.

Without this, you end up sprinkling raw column names everywhere. That feels fast for five minutes and painful forever after.

### Instructor Demo

Define the standard names we want:

```python
STANDARD_FIELDS = [
    "plot",
    "treatment",
    "crop",
    "replicate",
    "date",
    "yield_value",
    "yield_unit",
    "energy_value",
    "energy_unit",
]
```

Start with a placeholder column map:

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

Print candidate columns:

```python
for name, df in tables.items():
    print(f"\n{name}")
    for column in df.columns:
        print("  ", column)
```

Rename columns using the map:

```python
def clean_column_name(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def rename_with_contract(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    rename_map = {
        raw_column: standard_column
        for standard_column, raw_column in column_map.items()
        if raw_column in df.columns
    }

    renamed = df.rename(columns=rename_map).copy()
    renamed.columns = [clean_column_name(col) for col in renamed.columns]
    return renamed
```

### Your Turn

Update `COLUMN_MAP` based on the actual dataset columns.

If a field does not exist, leave it out of the analysis and write a note.

### Checkpoint

You should be able to choose the crop table and rename its important columns to standard names.

Example:

```python
crop_table_name = "replace_with_actual_table_name"
crop_raw = tables[crop_table_name]
crop_renamed = rename_with_contract(crop_raw, COLUMN_MAP)

print(crop_renamed.columns)
```

### Recap

The contract is where the pipeline becomes intentional. We are not letting random source headers leak into every step.

## Break: 10 Minutes

When you come back, we stop looking at the data and start shaping it.

## Module 4: Clean And Standardize

### Big Idea

Grouping only works when labels are consistent. `Tomato`, `tomatoes`, and ` tomato ` may mean the same crop to a human, but pandas will treat them as different categories.

Computers are fast, not wise. Help them out.

### Instructor Demo

Create text helpers:

```python
def clean_text(value):
    if pd.isna(value):
        return value
    return str(value).strip().lower().replace("_", " ")
```

Standardize crops:

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

Standardize treatments:

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

Clean the crop table:

```python
def clean_pipeline_table(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    if "crop" in cleaned.columns:
        cleaned["crop"] = cleaned["crop"].apply(standardize_crop)

    if "treatment" in cleaned.columns:
        cleaned["treatment"] = cleaned["treatment"].apply(standardize_treatment)

    if "date" in cleaned.columns:
        cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")

    for column in ["yield_value", "energy_value"]:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    return cleaned


crop_clean = clean_pipeline_table(crop_renamed)
crop_clean.head()
```

Inspect the cleaned values:

```python
for column in ["crop", "treatment"]:
    if column in crop_clean.columns:
        print(column, sorted(crop_clean[column].dropna().unique()))
```

### Your Turn

Extend `standardize_crop()` and `standardize_treatment()` if your raw values need more mappings.

### Checkpoint

You should have a cleaned crop table with consistent crop and treatment names.

### Recap

Cleaning is not just removing bad rows. It is making meaning consistent enough for analysis.

## Module 5: Validate Before Trusting

### Big Idea

Validation is the part of the pipeline that says, "No, we are not shipping nonsense today."

An automated pipeline without validation can produce wrong outputs faster than a manual process. That is not progress.

### Instructor Demo

Create validation helpers:

```python
def validate_required_columns(df: pd.DataFrame, required_columns: list[str]) -> list[str]:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        return [f"Missing required columns: {missing}"]
    return []


def validate_allowed_values(df: pd.DataFrame, column: str, allowed_values: set[str]) -> list[str]:
    if column not in df.columns:
        return []

    actual_values = set(df[column].dropna().astype(str))
    invalid_values = sorted(actual_values - allowed_values)

    if invalid_values:
        return [f"Unexpected values in {column}: {invalid_values}"]
    return []


def validate_non_negative(df: pd.DataFrame, columns: list[str]) -> list[str]:
    errors = []

    for column in columns:
        if column in df.columns and (df[column] < 0).any():
            errors.append(f"{column} contains negative values")

    return errors
```

Run validation:

```python
ALLOWED_CROPS = {"tomato", "chilli pepper", "eggplant"}
ALLOWED_TREATMENTS = {"open_sun_control", "agrivoltaic", "ground_mounted_pv"}

errors = []
errors.extend(validate_required_columns(crop_clean, ["crop", "treatment", "yield_value"]))
errors.extend(validate_allowed_values(crop_clean, "crop", ALLOWED_CROPS))
errors.extend(validate_allowed_values(crop_clean, "treatment", ALLOWED_TREATMENTS))
errors.extend(validate_non_negative(crop_clean, ["yield_value", "energy_value"]))

if errors:
    for error in errors:
        print("ERROR:", error)
else:
    print("Validation passed")
```

Save the validation report:

```python
validation_report = pd.DataFrame({
    "status": ["error"] * len(errors) if errors else ["ok"],
    "message": errors if errors else ["Validation passed"],
})

validation_report.to_csv(REPORTS_DIR / "validation_report.csv", index=False)
```

### Your Turn

Add one more validation check. Pick one:

- duplicate records
- missing yield values
- unparseable dates
- zero values that need review
- unexpected plot names

### Checkpoint

You should have:

```text
outputs/reports/validation_report.csv
```

### Recap

Validation is where the pipeline earns trust. If the data fails, we want a clear message, not a mysterious chart.

## Module 6: Transform Into Crop Insights

### Big Idea

Transformation turns cleaned records into decision-ready tables.

We are not asking pandas to tell us the meaning of agriculture. We are asking it to summarize the evidence clearly enough for humans to discuss.

### Instructor Demo

Summarize crop performance:

```python
def summarize_crop_performance(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = ["crop", "treatment", "yield_value"]
    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Cannot summarize crop performance. Missing columns: {missing}")

    return (
        df
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


crop_summary = summarize_crop_performance(crop_clean)
crop_summary
```

Compare agrivoltaic against open-sun control:

```python
def compare_treatments(summary: pd.DataFrame) -> pd.DataFrame:
    comparison = (
        summary
        .pivot(index="crop", columns="treatment", values="mean_yield")
        .reset_index()
    )

    if {"agrivoltaic", "open_sun_control"}.issubset(comparison.columns):
        comparison["yield_difference"] = (
            comparison["agrivoltaic"] - comparison["open_sun_control"]
        )
        comparison["yield_difference_pct"] = (
            comparison["yield_difference"] / comparison["open_sun_control"] * 100
        ).round(2)

    return comparison


treatment_comparison = compare_treatments(crop_summary)
treatment_comparison
```

Save outputs:

```python
crop_summary.to_csv(PROCESSED_DIR / "crop_performance_summary.csv", index=False)
treatment_comparison.to_csv(PROCESSED_DIR / "treatment_comparison.csv", index=False)
```

Create charts:

```python
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))
sns.barplot(data=crop_summary, x="crop", y="mean_yield", hue="treatment")
plt.title("Mean Crop Yield by Treatment")
plt.xlabel("Crop")
plt.ylabel("Mean yield")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "mean_crop_yield_by_treatment.png", dpi=150)
plt.close()
```

Optional difference chart:

```python
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
```

### Your Turn

Answer:

- Which crop performs best under agrivoltaic conditions?
- Which crop performs best under open-sun control?
- Which crop has the largest percentage difference?
- Are the observation counts balanced?

### Checkpoint

You should have:

```text
data/processed/crop_performance_summary.csv
data/processed/treatment_comparison.csv
outputs/charts/mean_crop_yield_by_treatment.png
```

### Recap

We started with raw files. We now have processed tables and charts. That is the core arc of a data pipeline.

## Optional: Energy Summary

If the dataset includes energy fields, summarize them separately:

```python
def summarize_energy(df: pd.DataFrame) -> pd.DataFrame:
    if "energy_value" not in df.columns:
        raise ValueError("No energy_value column found")

    group_columns = ["treatment"]
    if "plot" in df.columns:
        group_columns = ["plot", "treatment"]

    return (
        df
        .dropna(subset=["energy_value"])
        .groupby(group_columns, dropna=False)
        .agg(
            observations=("energy_value", "count"),
            mean_energy=("energy_value", "mean"),
            total_energy=("energy_value", "sum"),
        )
        .reset_index()
    )
```

Save the output:

```python
energy_summary.to_csv(PROCESSED_DIR / "energy_summary.csv", index=False)
```

## Wrap-Up: Responsible Interpretation

A clean pipeline does not make the dataset bigger than it is.

Be careful with claims:

- This is a Ghana pilot dataset.
- It should not be generalized to every farm in Ghana.
- Agrivoltaics decisions also depend on costs, maintenance, land tenure, crop markets, water access, and farmer priorities.
- The dataset requires attribution under CC-BY 4.0.

Good conclusion style:

> In this dataset, crop performance under agrivoltaic conditions appears to differ by crop. The pipeline can support discussion and further analysis, but more field trials and economic data are needed before making broad farmer or policy recommendations.

## Final Deliverables

By the end of the workshop, you should have:

- raw files in `data/raw/`
- profiling reports in `outputs/reports/`
- a validation report in `outputs/reports/`
- processed crop summaries in `data/processed/`
- at least one chart in `outputs/charts/`
- clear notes on what the data can and cannot support

