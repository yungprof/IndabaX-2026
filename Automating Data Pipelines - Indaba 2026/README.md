# Automating Data Pipelines - Indaba 2026

## Workshop Theme

**Automating a Ghana Agrivoltaics Data Pipeline**

This is a 3-hour, code-along workshop that teaches participants how to build a repeatable data pipeline using a real agriculture dataset from Ghana. The tutorial is centered on agrivoltaics: farming under or near solar photovoltaic panels so that the same land can support both crop production and clean energy generation.

The teaching rhythm is practical:

```text
demo
build
inspect
fix
checkpoint
```

## Main Problem

**Can Ghanaian farms combine solar power generation with crop production without reducing harvest performance?**

Participants will use tabular field data to compare crop performance under raised solar panels against open-sun farming conditions. The goal is not only to analyze the data, but to learn how a raw dataset becomes trusted, validated, analysis-ready output through an automated pipeline.

## Dataset

The workshop uses an agriculture dataset from the FAIR Forward Open Data and Use Cases catalog.

- Catalog: https://fair-forward.github.io/datasets/
- Dataset: https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
- Country: Ghana
- Data type: Tabular
- Crops: tomatoes, chilli pepper, and eggplant
- Theme: crop yield, solar energy, food security, and climate adaptation
- License: CC-BY 4.0
- Provider: Responsible AI Lab, KNUST

The dataset compares three experimental setups:

- Open-sun control plot with no solar PV panels
- Agrivoltaic plot with raised solar PV panels above crops
- Traditional ground-mounted solar PV on bare land

## What Learners Will Build

Learners will build a pipeline that:

1. Organizes raw dataset files.
2. Loads tabular data into Python.
3. Profiles columns, missing values, and data types.
4. Defines a simple data contract.
5. Cleans crop, plot, treatment, date, yield, and energy fields.
6. Validates required fields and measurement rules.
7. Transforms raw data into analysis-ready tables.
8. Compares agrivoltaic crop performance with open-sun control performance.
9. Saves processed outputs and charts.
10. Runs the workflow as a repeatable pipeline.

## Folder Structure

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
    ghana_agrivoltaics_pipeline.ipynb
  src/
    ingest.py
    profile_data.py
    validate_data.py
    transform.py
    run_pipeline.py
  outputs/
    charts/
    reports/
```

## Material Guide

- `01_Tutorial_Guide.md`: learner-facing tutorial with the step-by-step pipeline workflow.
- `02_Facilitator_Guide.md`: 3-hour pacing, teaching notes, prompts, checkpoints, and common issues.
- `03_Exercises.md`: module-aligned live tasks, checkpoints, and stretch exercises.
- `requirements.txt`: Python packages needed for the workshop.
- `notebooks/ghana_agrivoltaics_pipeline.ipynb`: guided code-along notebook.
- `data/raw/`: place the downloaded Kaggle dataset files here.
- `data/processed/`: cleaned and transformed outputs will be written here.
- `src/`: reusable pipeline scripts.
- `outputs/charts/`: generated charts.
- `outputs/reports/`: profiling and validation reports.

## 3-Hour Flow

| Time | Segment | Outcome |
| --- | --- | --- |
| 0:00-0:15 | Opening | Ghana agriculture problem and dataset context |
| 0:15-0:35 | Module 1 | Raw files loaded |
| 0:35-1:05 | Module 2 | Tables inspected and profiled |
| 1:05-1:30 | Module 3 | Data contract drafted |
| 1:30-1:40 | Break | Reset and catch up |
| 1:40-2:05 | Module 4 | Fields cleaned and standardized |
| 2:05-2:30 | Module 5 | Validation report produced |
| 2:30-2:50 | Module 6 | Crop summaries and charts created |
| 2:50-3:00 | Wrap | Responsible interpretation |

## Recommended Setup

Create a Python environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, `python` may be the correct command instead of `python3`.

Download the dataset manually from Kaggle and place the extracted files in:

```text
data/raw/
```

If the Kaggle CLI is configured, the dataset can also be downloaded with:

```bash
kaggle datasets download responsibleailab/agrivoltaic-dataset-ghana -p data/raw --unzip
```

## Responsible Data Use

This dataset comes from a Ghanaian pilot and should not be treated as proof that agrivoltaics will work the same way across all farms, regions, soils, crop varieties, or economic conditions.

Participants should:

- Credit the dataset provider and source catalog.
- Avoid overgeneralizing from one pilot dataset.
- Communicate uncertainty clearly.
- Consider farmer context, land use, costs, maintenance, and market access.
- Treat pipeline outputs as decision support, not final policy or farming advice.

## Workshop Outcome

By the end of the workshop, participants should understand how to turn a real agriculture dataset into a reliable, repeatable data pipeline that can support crop and energy analysis in Ghana.
