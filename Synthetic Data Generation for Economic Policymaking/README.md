# Synthetic Data Generation for Economic Policymaking

**IndabaX Ghana 2026 tutorial — sponsored by the African Center for Economic Transformation (ACET).**

A hands-on workshop on **two-sample synthetic data generation**: using the Ghana Living Standards
Survey (GLSS6, 2012/13) to synthesize welfare and poverty variables into the Ghana Demographic
and Health Survey (DHS 2014), then analyzing child-health outcomes by synthetic poverty status.

## What's in this repository

| Item | File |
|---|---|
| Theory slides | `part1-synthetic-data-tutorial-theory-indabax-2026.pdf` |
| Practical manual slides | `part2-synthetic-data-tutorial-practical-slides-indabax-2026.pdf` — a self-paced manual for the notebook |
| Participant practical notebook | `part2-synthetic-data-tutorial-practical-indabax-2026.Rmd` — runs the whole workflow in-notebook |
| Plain R script | `part2-synthetic-data-tutorial-practical-script-indabax-2026.R` — same practical code, generated from the notebook for line-by-line use |
| Interactive WebR app (no R install) | `webr/part2-synthetic-data-tutorial-practical-webr-indabax-2026.html` (source: `.qmd`) — runs R in your browser; fetches the workshop data from a hosted URL |
| Class activity worksheet | `docs/synthetic-data-activity-handout.pdf` — Parts A-B |
| Practical group challenge | `docs/synthetic-data-practical-challenge.pdf` — group validity memo with submission instructions |
| Variable codebook | `docs/codebook-teaching-data.pdf` |

## Quick start

**First, get the repo onto your computer.** Use GitHub's **Code -> Download ZIP** button, or clone
the repository. Open the unzipped/cloned folder as your working folder.

**Just want to read it?** Open `part1-synthetic-data-tutorial-theory-indabax-2026.pdf` (the theory)
and `part2-synthetic-data-tutorial-practical-slides-indabax-2026.pdf` (a step-by-step manual of
what the notebook does).

**Want to run it locally?** You need R and the prepared data extract (see *The data* below).
Open the `.Rmd` notebook for the guided version, or open the plain `.R` script if you prefer to
run the same code line by line in RStudio.

```r
install.packages(c("mice", "dplyr", "ggplot2", "rmarkdown", "kableExtra", "tidyr"))
rmarkdown::render("part2-synthetic-data-tutorial-practical-indabax-2026.Rmd",
                  output_format = "html_document")

# Optional: run the plain R script instead of knitting the notebook.
source("part2-synthetic-data-tutorial-practical-script-indabax-2026.R")
```

The notebook has **scale knobs** in its YAML `params` (`subsample_train`, `subsample_holdout`,
`subsample_dhs`, `m_implicates`, `maxit`) — reduce them for a faster run while exploring.

**No R installation?** Open `webr/part2-synthetic-data-tutorial-practical-webr-indabax-2026.html`. The WebR
version computes in your browser on smaller hosted CSVs generated from the same workshop extract.

## The data

The raw **GLSS6 and DHS 2014 microdata are licensed and are not included in this repository.** To prepare you rown 
raw files for your own projects, contact the following sources:

- **DHS 2014:** register and download from [The DHS Program](https://dhsprogram.com/).
- **GLSS6:** register and download from the Ghana Statistical Service / World Bank LSMS catalog.

Workshop attendees receive a prepared teaching extract through the Dropbox link below during the
practical session. The link may be empty or inactive before and after the event. 

**Workshop Dropbox data link:** [Download the workshop data](https://www.dropbox.com/scl/fo/pkiom85yjznl0id9692tn/AGbkZPzFT9Zt9ynIrJnfy2Y?rlkey=8jlbhksqa9o67nwio55ycu1c8&st=8q7577ig&dl=0)

Download `acet-indabax-2026-local-data.zip` from that link and unzip it at the root of this
repository, not inside a separate subfolder. After unzipping, the notebook should find the extract
files in `data/practical/teaching/`. The variable manifest is already included at
`output/diagnostics/practical_variable_manifest.csv`.

The local notebook uses the full prepared RDS files:

- `teach_glss6_train.rds`
- `teach_glss6_holdout.rds`
- `teach_dhs2014_households.rds`
- `teach_dhs2014_children.rds`

Quick check from R:

```r
file.exists("data/practical/teaching/teach_glss6_train.rds")
```

If this returns `TRUE`, the local notebook can find the data.

The WebR version uses hosted CSVs (`webr_glss_train.csv`, `webr_glss_holdout.csv`,
`webr_dhs_households.csv`, `webr_dhs_children.csv`) that are subsampled from the same teaching
extract for browser speed. Those CSVs live in a separate temporary workshop data repository, not in
this permanent code/materials repository.

## What participants do

1. Warm up on the two surveys — what each observes and lacks.
2. Define the welfare target, derived poverty status, the NHIS target, and shared predictors.
3. Fit the synthesis model in GLSS and transport welfare/NHIS into DHS.
4. Analyze DHS child stunting by overall and imputed poverty status.
5. Pool estimates with Rubin-style within/between variance.
6. Validate synthetic welfare against the GLSS holdout (ground truth).
7. Run a DHS calibration check on an observed variable (transport).
8. Inspect optional model-design and engine-sensitivity appendix checks.

The optional **engine sensitivity** appendix lets you swap the synthesis engine (`norm`, `pmm`,
`cart`, `rf`) and compare.

## Facilitators

- **Austin Denteh** — Department of Economics, Davidson College
- **Prince Baah** — Lecturer, Department of Economics, Ashesi University
- **Blaise Bayuo** — Senior Fellow, African Center for Economic Transformation

## License

Materials (slides, worksheet, codebook): **CC BY 4.0**. Code: **MIT**. See `LICENSE`.

## Citation

> Denteh, A., Baah, P., & Bayuo, B. (2026). *Synthetic Data Generation for Economic Policymaking.*
> IndabaX Ghana 2026 tutorial, sponsored by ACET.
