# 02 Facilitator Guide

# 3-Hour Code-Along Workshop

## Workshop Title

**Automating a Ghana Agrivoltaics Data Pipeline**

## Teaching Style

Run this like a practical code-along workshop:

- move quickly but pause at checkpoints
- demo first, then make learners do the thing
- explain concepts through the code they are writing
- let learners inspect real data instead of hiding the mess
- keep the energy high, but keep the claims careful

Do not present this like a long lecture. The room should be building for most of the session.

The vibe:

> We are going to take raw agriculture data, make it behave, and produce outputs we can actually discuss.

## Core Story

The sponsors want the tutorial to use agricultural data from the FAIR Forward catalog. We selected the Ghana agrivoltaics dataset because it is practical, tabular, Ghana-specific, and connected to food security and clean energy.

Main question:

> Can Ghanaian farms combine solar power generation with crop production without reducing harvest performance?

Pipeline question:

> What has to happen before raw field data becomes trustworthy evidence?

## Audience Assumptions

Learners should know basic Python. They do not need advanced data engineering or machine learning experience.

They should be able to:

- run Python cells or scripts
- read simple pandas code
- inspect DataFrames
- understand basic grouping and aggregation

## Pre-Workshop Prep

Do this before teaching:

1. Download the dataset from Kaggle.
2. Unzip it and inspect the real files.
3. Confirm which table contains crop performance.
4. Confirm the real column names.
5. Prepare a working `COLUMN_MAP`.
6. Test the environment with `pip install -r requirements.txt`.
7. Run through the tutorial once.
8. Keep a local copy of the dataset in case internet access fails.

Dataset:

https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana

Catalog:

https://fair-forward.github.io/datasets/

## 3-Hour Run Of Show

| Time | Segment | Format | Outcome |
| --- | --- | --- | --- |
| 0:00-0:15 | Cold open | Story + discussion | Learners understand the Ghana problem |
| 0:15-0:35 | Module 1 | Demo + code-along | Raw files are loaded |
| 0:35-1:05 | Module 2 | Demo + exercise | Tables are inspected and profiled |
| 1:05-1:30 | Module 3 | Guided mapping | Data contract is drafted |
| 1:30-1:40 | Break | Reset | Everyone catches up |
| 1:40-2:05 | Module 4 | Demo + code-along | Fields are cleaned and standardized |
| 2:05-2:30 | Module 5 | Demo + exercise | Validation report is produced |
| 2:30-2:50 | Module 6 | Demo + code-along | Crop summaries and charts are created |
| 2:50-3:00 | Wrap | Discussion | Learners interpret outputs responsibly |

## Opening: 0:00-0:15

### Goal

Make the problem feel real before touching code.

### Suggested Opening

> Today we are not starting with a toy sales CSV. We are using Ghana agriculture data from the FAIR Forward catalog. The question is whether farms can produce crops and solar energy on the same land. But before we discuss recommendations, we need a pipeline that turns raw data into something trustworthy.

### Ask The Room

- What could go wrong if this data is messy?
- Who might use the output of this analysis?
- What would make the output trustworthy?

### Teaching Note

Keep this short. The code is the workshop. The story gives the code stakes.

## Module 1: Load Raw Files, 0:15-0:35

### Big Idea

The first job of a pipeline is to reliably find and load inputs.

### Demo

Show:

- project folders
- `Path`
- `data/raw/`
- loading CSV and Excel files into a dictionary

### Learner Task

Learners list raw files and load tables.

### Checkpoint

Ask:

- Who has files listed?
- Who has a `tables` dictionary?
- Who can print table names and shapes?

### Common Issues

| Issue | Fix |
| --- | --- |
| No files found | Check that the dataset was extracted into `data/raw/` |
| Kaggle download fails | Use the backup dataset |
| Excel fails to load | Confirm `openpyxl` is installed |

## Module 2: Inspect And Profile, 0:35-1:05

### Big Idea

Raw data gets inspected before it gets trusted.

### Demo

Show:

- `df.head()`
- `df.shape`
- column lists
- data types
- missing value profile
- unique counts

### Learner Task

Learners identify:

- likely crop table
- likely energy table
- crop column
- treatment column
- yield or measurement column
- suspicious missingness

### Checkpoint

Everyone should save at least one profile CSV to:

```text
outputs/reports/
```

### Teaching Line

> Profiling is not paperwork. It is where we stop pretending and start reading the actual dataset.

## Module 3: Data Contract, 1:05-1:30

### Big Idea

Pipelines need stable internal names even when raw source columns are messy.

### Demo

Show:

- standard fields
- placeholder `COLUMN_MAP`
- raw-to-standard renaming

### Learner Task

Learners fill in `COLUMN_MAP` for the crop table.

### Checkpoint

Ask:

- What is your crop column?
- What is your treatment column?
- What is your yield column?
- Which field was ambiguous?

### Common Issue

Learners may want you to give them the mapping immediately. Let them inspect first. The point is to practice reading unfamiliar data.

## Break: 1:30-1:40

Use this time to help anyone who is behind on:

- file paths
- loading data
- choosing the crop table
- column mapping

## Module 4: Clean And Standardize, 1:40-2:05

### Big Idea

Analysis requires consistent meaning. Labels need to be normalized before grouping.

### Demo

Show:

- `clean_text`
- `standardize_crop`
- `standardize_treatment`
- `pd.to_datetime`
- `pd.to_numeric`

### Learner Task

Learners clean the crop table and print unique crop and treatment values.

### Checkpoint

The cleaned crop table should have consistent labels for:

- tomato
- chilli pepper
- eggplant
- open-sun control
- agrivoltaic
- ground-mounted PV, if present

### Common Issue

If labels do not match expected values, extend the mapping function. Do not manually edit the raw file.

## Module 5: Validate Data, 2:05-2:30

### Big Idea

Automated workflows must fail clearly when the data violates expectations.

### Demo

Show:

- required column validation
- allowed crop validation
- allowed treatment validation
- non-negative numeric validation
- saving `validation_report.csv`

### Learner Task

Learners run validation and add one extra validation rule.

Possible rules:

- duplicate checks
- missing yield checks
- date parsing checks
- unexpected plot checks

### Checkpoint

Everyone should have:

```text
outputs/reports/validation_report.csv
```

### Discussion Prompt

> If this pipeline ran every Monday morning, should it fail on bad data or quietly produce the report?

Expected answer:

Fail clearly, or at minimum warn loudly and mark the output as incomplete.

## Module 6: Transform And Visualize, 2:30-2:50

### Big Idea

The pipeline turns cleaned data into decision-ready outputs.

### Demo

Show:

- group by crop and treatment
- mean and median yield
- treatment comparison pivot
- percentage difference
- chart creation
- saving CSVs and PNGs

### Learner Task

Learners produce:

```text
data/processed/crop_performance_summary.csv
data/processed/treatment_comparison.csv
outputs/charts/mean_crop_yield_by_treatment.png
```

### Checkpoint

Ask:

- Which crop performs best under agrivoltaic conditions?
- Which crop performs best under open-sun control?
- Is the comparison balanced?

## Wrap: 2:50-3:00

### Goal

Help learners interpret responsibly.

### Ask

- What does the data suggest?
- What can we not conclude?
- What extra data would strengthen the decision?
- Who should be involved before recommending agrivoltaics?

### Key Responsible Data Points

- This is a pilot dataset.
- It does not represent all farms in Ghana.
- Costs and farmer context matter.
- Land tenure and maintenance matter.
- Water, soil, and market access matter.
- Attribution is required under CC-BY 4.0.

### Closing Line

> The win today is not just the chart. The win is the workflow: inspect, contract, clean, validate, transform, and communicate the limits.

## Instructor Energy Notes

Use strong, practical framing:

- "Trust the file only after it has earned it."
- "If the labels are inconsistent, your groupby will happily lie to your face."
- "A chart is not an argument unless the pipeline behind it is defensible."
- "Validation is where bad assumptions go to be noticed."

Keep humor pointed at the workflow, not at learners.

## What Not To Do

- Do not spend 45 minutes lecturing before code.
- Do not hide messy column names from learners.
- Do not overclaim the agricultural result.
- Do not turn the session into computer vision or advanced ML.
- Do not manually fix the raw dataset.

## Success Criteria

By the end, learners should have:

- loaded the raw dataset
- profiled at least one table
- created a column map
- cleaned crop and treatment fields
- generated a validation report
- produced crop summary and treatment comparison outputs
- created at least one chart
- written a careful interpretation

