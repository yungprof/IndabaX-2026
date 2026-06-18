# Synthetic Data Generation for Economic Policymaking
# Plain R script version for IndabaX Ghana 2026.
# Generated from part2-synthetic-data-tutorial-practical-indabax-2026.Rmd.
# Edit the RMarkdown notebook in the source repo, then rebuild the public export.

params <-
list(subsample_train = 0L, subsample_holdout = 0L, subsample_dhs = 0L, 
    m_implicates = 5L, maxit = 5L)

## ----setup, include=FALSE-----------------------------------------------------
knitr::opts_chunk$set(
  echo = TRUE,
  message = FALSE,
  warning = FALSE,
  fig.width = 8,
  fig.height = 4.8
)

library(dplyr)
library(ggplot2)
library(mice)

source("code/utils/project_paths.R")

# ---- SCALE KNOBS (set in the YAML params above) --------------------------
# subsample_train / subsample_holdout / subsample_dhs: 0 = use ALL rows;
#   a positive number subsamples that many rows (fixed seed) to speed up the
#   live mice fit. m_implicates / maxit control the number of imputed datasets and
#   chained-equation iterations. mice cycles because each conditional model uses
#   current draws of the other incomplete variables; repeated cycles let the
#   welfare and NHIS draws settle into a mutually consistent imputed data set.
#   Full real-data run: 0 / 0 / 0 / 5 / 5.
#   Fast classroom demo, e.g.: 3000 / 1000 / 3000 / 3 / 2.
# --------------------------------------------------------------------------
DATA_FAMILY <- "teaching"
# Source: GLSS6 poverty/welfare aggregate file
# AGGREGATES/POV_GHA_2013_GLSS6-updated.dta, variables
# poveline_fd_2013 (extreme poverty line per year) and
# poveline_2013 (absolute poverty line per year).
POV_EXTREME <- 792.05
POV_ABSOLUTE <- 1314
SYNTH_SEED <- 20260614
EXTENSION_SEED <- 20260616
M <- params$m_implicates
MAXIT <- params$maxit

input_dir <- project_path("data", "practical", "teaching")
input_prefix <- "teach_"

diag_dir <- project_path("output", "diagnostics")

need_file <- function(path) {
  if (!file.exists(path)) stop("Missing required file: ", path, call. = FALSE)
  path
}

read_input <- function(name) {
  readRDS(need_file(file.path(input_dir, paste0(input_prefix, name, ".rds"))))
}

# ---- WEIGHTING HELPERS ---------------------------------------------------
# Every rate we REPORT is survey-weighted. (Slide "Decisions for every imputed
# variable": the model is fit unweighted, but summaries and
# all validation statistics carry household_weight.) These helpers centralise
# that rule so no chunk forgets the weights.

# Weighted mean that drops NA in either x or the weight.
w_mean <- function(x, w) {
  ok <- !is.na(x) & !is.na(w)
  if (!any(ok)) return(NA_real_)
  weighted.mean(x[ok], w[ok])
}

# Weighted mean of a 0/1 indicator, expressed as a percentage.
w_rate <- function(x, w) 100 * w_mean(as.numeric(x), w)

# Weighted category shares for one variable, tidy long format (for side-by-side
# GLSS vs DHS comparisons in the warm-up).
w_tab <- function(dat, var, weight = "household_weight", source_label = NULL) {
  d <- dat %>%
    filter(!is.na(.data[[var]]), !is.na(.data[[weight]])) %>%
    mutate(value = as.character(.data[[var]]))
  d %>%
    group_by(value) %>%
    summarise(n = n(),
              pct_w = 100 * sum(.data[[weight]]) / sum(d[[weight]]),
              .groups = "drop") %>%
    mutate(variable = var, survey = source_label, pct_w = round(pct_w, 1)) %>%
    select(survey, variable, value, pct_w, n)
}

# ---- RUBIN'S RULES POOLING -----------------------------------------------
# Combine an estimate computed on each of the m imputed datasets into one number with
# correct uncertainty. (Slide "Multiple imputation keeps uncertainty visible"
# and backup slide "Combining estimates across imputed datasets".)
#   qbar  = average of the m point estimates
#   ubar  = average WITHIN-imputation variance (uncertainty if welfare were known)
#   b     = BETWEEN-imputation variance        (extra uncertainty from imputing it)
#   total = ubar + (1 + 1/m) * b               (Rubin's total variance)
pool_scalar <- function(q, u) {
  m <- length(q)
  qbar <- mean(q, na.rm = TRUE); ubar <- mean(u, na.rm = TRUE)
  b <- stats::var(q, na.rm = TRUE)
  total <- ubar + (1 + 1 / m) * b
  data.frame(estimate = qbar, within_var = ubar, between_var = b,
             total_var = total, se = sqrt(total))
}

# Weighted proportion plus its within-imputation variance, using an effective
# sample size (Kish) for the weights. Feeds the WITHIN term of pool_scalar().
weighted_binary_est <- function(x, w) {
  ok <- !is.na(x) & !is.na(w)
  x <- as.numeric(x[ok]); w <- w[ok]
  p <- weighted.mean(x, w)
  n_eff <- sum(w)^2 / sum(w^2)
  data.frame(estimate = p, var = p * (1 - p) / n_eff)
}

# Recovery metrics for the holdout: how close are imputed (log) welfare draws to
# the TRUE held-out welfare? Used by the engine-switch extension.
recovery_metrics <- function(dat, label) {
  dat %>%
    group_by(.imp) %>%
    summarise(
      mae_log = mean(abs(synth_log_welfare - log(true_welfare)), na.rm = TRUE),
      rmse_log = sqrt(mean((synth_log_welfare - log(true_welfare))^2, na.rm = TRUE)),
      corr_log = cor(synth_log_welfare, log(true_welfare), use = "complete.obs"),
      synth_poverty_rate_w = w_rate(synth_poor, household_weight),
      true_poverty_rate_w = w_rate(true_poor, household_weight),
      .groups = "drop"
    ) %>%
    summarise(engine = label, mae_log = mean(mae_log), rmse_log = mean(rmse_log),
              corr_log = mean(corr_log),
              synth_poverty_rate_w = mean(synth_poverty_rate_w),
              true_poverty_rate_w = mean(true_poverty_rate_w), .groups = "drop")
}


## ----load-data----------------------------------------------------------------
# Four prepared teaching files = the four corners of the design (slide
# "Our two data sources: GLSS and DHS"):
#   glss_train     GLSS6 rows that TRAIN the model  (X and welfare Y both observed)
#   glss_holdout   GLSS6 rows held out for Validation Check 1 (welfare known, but we hide it)
#   dhs_households the records to be ENRICHED        (X only; welfare missing by design)
#   dhs_children  child outcomes linked to DHS households (the analysis outcomes)
glss_train <- read_input("glss6_train")
glss_holdout <- read_input("glss6_holdout")
dhs_households <- read_input("dhs2014_households")
dhs_children <- read_input("dhs2014_children")

# Apply the scale knobs (0 = use all rows). Children follow the DHS subsample.
set.seed(SYNTH_SEED)
if (params$subsample_train  > 0 && params$subsample_train  < nrow(glss_train))
  glss_train    <- glss_train    %>% slice_sample(n = params$subsample_train)
if (params$subsample_holdout > 0 && params$subsample_holdout < nrow(glss_holdout))
  glss_holdout  <- glss_holdout  %>% slice_sample(n = params$subsample_holdout)
if (params$subsample_dhs    > 0 && params$subsample_dhs    < nrow(dhs_households))
  dhs_households <- dhs_households %>% slice_sample(n = params$subsample_dhs)
dhs_children <- dhs_children %>% filter(hh_key %in% dhs_households$hh_key)

surface_counts <- data.frame(
  file = c("GLSS train households", "GLSS holdout households",
           "DHS target households", "DHS children"),
  rows = c(nrow(glss_train), nrow(glss_holdout),
           nrow(dhs_households), nrow(dhs_children)),
  columns = c(ncol(glss_train), ncol(glss_holdout),
              ncol(dhs_households), ncol(dhs_children))
)

knitr::kable(surface_counts)


## ----observed-missing-map-----------------------------------------------------
# This is the "missing-data framework" slide in table form: each concept is
# Observed or Missing in each file. The whole exercise is filling the
# "Missing by design" cells in DHS using the GLSS-learned model.
observed_map <- data.frame(
  concept = c("Shared household predictors",
              "Welfare aggregate",
              "Derived poverty status",
              "Any household member registered with NHIS",
              "DHS wealth benchmark",
              "Child nutrition and illness outcomes"),
  glss = c("Observed", "Observed", "Observed from welfare",
           "Observed", "Not observed", "Not observed"),
  dhs_households = c("Observed", "Missing by design",
                     "Missing by design", "Observed (transport target)",
                     "Observed", "Household link only"),
  dhs_children = c("Linked through household", "Not observed",
                   "Not observed", "Linked through household",
                   "Linked through household", "Observed")
)

knitr::kable(observed_map)


## ----shared-predictor-summary-------------------------------------------------
binary_summary <- data.frame(
  survey = c("GLSS train", "DHS households"),
  urban_pct_w = c(
    w_rate(glss_train$urban, glss_train$household_weight),
    w_rate(dhs_households$urban, dhs_households$household_weight)
  ),
  electricity_pct_w = c(
    w_rate(glss_train$has_electricity, glss_train$household_weight),
    w_rate(dhs_households$has_electricity, dhs_households$household_weight)
  ),
  female_head_pct_w = c(
    w_rate(glss_train$head_female, glss_train$household_weight),
    w_rate(dhs_households$head_female, dhs_households$household_weight)
  ),
  mean_hh_size_w = c(
    w_mean(glss_train$hh_size, glss_train$household_weight),
    w_mean(dhs_households$hh_size, dhs_households$household_weight)
  )
) %>%
  mutate(across(where(is.numeric), ~ round(.x, 1)))

knitr::kable(binary_summary)


## ----region-side-by-side------------------------------------------------------
region_summary <- bind_rows(
  w_tab(glss_train, "region10", source_label = "GLSS train"),
  w_tab(dhs_households, "region10", source_label = "DHS households")
) %>%
  select(variable, value, survey, pct_w) %>%
  tidyr::pivot_wider(names_from = survey, values_from = pct_w)

knitr::kable(region_summary)


## ----material-side-by-side----------------------------------------------------
housing_summary <- bind_rows(
  w_tab(glss_train, "floor_material_screen", source_label = "GLSS train"),
  w_tab(dhs_households, "floor_material_screen", source_label = "DHS households"),
  w_tab(glss_train, "water_source_cat", source_label = "GLSS train"),
  w_tab(dhs_households, "water_source_cat", source_label = "DHS households")
) %>%
  select(variable, value, survey, pct_w) %>%
  tidyr::pivot_wider(names_from = survey, values_from = pct_w) %>%
  arrange(variable, value)

knitr::kable(housing_summary)


## ----warmup-welfare-nhis------------------------------------------------------
# First show welfare on its raw scale: the long right tail is the reason the
# imputation model works on log welfare.
ggplot(glss_train, aes(x = welfare)) +
  geom_histogram(bins = 45, fill = "#2f6f73", color = "white") +
  labs(x = "GLSS welfare, raw annual GHS per adult equivalent",
       y = "Households") +
  theme_minimal(base_size = 12)

# Then show the same variable on a log axis. This is why the model below
# imputes LOG welfare with a normal model and back-transforms with exp()
# (slides "Begin with single imputation" and "The imputation workflow at a glance").
ggplot(glss_train, aes(x = welfare)) +
  geom_histogram(bins = 45, fill = "#2f6f73", color = "white") +
  scale_x_log10() +
  labs(x = "GLSS welfare, log scale", y = "Households") +
  theme_minimal(base_size = 12)

nhis_warmup <- data.frame(
  survey = c("GLSS train", "DHS households"),
  nhis_any_member_registered_pct_w = c(
    w_rate(glss_train$nhis_any_member_registered, glss_train$household_weight),
    w_rate(dhs_households$nhis_any_member_registered,
           dhs_households$household_weight)
  )
) %>%
  mutate(nhis_any_member_registered_pct_w =
           round(nhis_any_member_registered_pct_w, 1))

knitr::kable(nhis_warmup)


## ----weighted-unweighted-demo-------------------------------------------------
weighted_unweighted <- data.frame(
  statistic = c("GLSS poverty rate", "GLSS urban share"),
  unweighted = c(
    mean(glss_train$welfare < POV_ABSOLUTE, na.rm = TRUE),
    mean(glss_train$urban, na.rm = TRUE)
  ),
  weighted = c(
    w_mean(glss_train$welfare < POV_ABSOLUTE, glss_train$household_weight),
    w_mean(glss_train$urban, glss_train$household_weight)
  )
) %>%
  mutate(across(c(unweighted, weighted), ~ round(100 * .x, 1)))

knitr::kable(weighted_unweighted)


## ----run-imputation-----------------------------------------------------------
# --- Which predictors X bridge the two surveys? --------------------------
# The manifest is the variable-role table from data prep (slide "Activity:
# sort variables before modeling"): predictor_core = the shared predictors X.
manifest <- read.csv(need_file(file.path(diag_dir, "practical_variable_manifest.csv")),
                     stringsAsFactors = FALSE)
core_pred <- manifest$variable[manifest$manifest_role == "predictor_core"]

# Drop three columns from the MODEL only (kept in the extract for inspection):
# they are exact linear combinations of other predictors, which makes the
# regression unstable. members_total ~ hh_size; adults_15plus = members_total -
# children_under15; floor_non_earth = duplicate of the floor_material_screen dummy.
collinear_drop <- c("members_total", "adults_15plus", "floor_non_earth")
model_pred <- setdiff(core_pred, collinear_drop)

# cat_predictors is a helper list of categorical predictors that should be converted to factors before mice runs
cat_predictors <- intersect(
  c("region10", "water_source_cat", "cooking_fuel_cat",
    "roof_material_cat", "floor_material_screen"), core_pred)

# DERIVE, don't draw (slide "From the welfare aggregate to poverty").
# Poverty is a deterministic cut of welfare at Ghana's official lines, applied
# AFTER each welfare draw — never modelled as its own outcome.
derive_poverty <- function(welfare) {
  cut(welfare, c(-Inf, POV_EXTREME, POV_ABSOLUTE, Inf),
      labels = c("Very poor", "Poor", "Non poor"))
}


# build_frame prepares the data that mice will see.It takes an “apply” dataset, 
# either the GLSS holdout or DHS households, and stacks it underneath glss_train.
# It also creates log_welfare and converts categorical variables into factors.
# Build the stacked frame mice will work on: GLSS train rows (.role "train",
# welfare observed) on top of the apply rows (.role "apply", welfare masked).
# Stacking is what lets one model be FIT on GLSS and PREDICTED into the apply
# rows (slide "Synthetic data is a missing data framework").
build_frame <- function(apply_dat, targets_to_mask, extra_cols = character(0)) {
  cols <- c("hh_key", "household_weight", core_pred,
            "welfare", "nhis_any_member_registered", extra_cols)
  tr <- glss_train %>% select(any_of(cols)) %>% mutate(.role = "train")
  ap <- apply_dat %>% select(any_of(cols)) %>% mutate(.role = "apply")
  stacked <- bind_rows(tr, ap) %>%
    mutate(log_welfare = ifelse(!is.na(welfare) & welfare > 0, log(welfare), NA_real_))
  # Hide the targets on the apply rows so mice treats them as "to be imputed".
  for (v in targets_to_mask) stacked[[v]][stacked$.role == "apply"] <- NA
  for (v in intersect(c(cat_predictors, "head_educ_cat", "toilet_type_screen"),
                      names(stacked))) stacked[[v]] <- factor(stacked[[v]])
  stacked$region10 <- factor(stacked$region10)
  stacked$nhis_any_member_registered <-
    factor(stacked$nhis_any_member_registered, levels = c(0, 1))
  if ("has_electricity" %in% names(stacked))
    stacked$has_electricity <- factor(stacked$has_electricity, levels = c(0, 1))
  stacked
}

# Fit mice and draw m imputed datasets. The three decisions from the slide
# "Decisions for every imputed variable" appear here:
#   (1) target_methods   = the ENGINE per target (norm for welfare, logreg for binary)
#   (2) target_predictors = the CONDITIONING set X for each target
#   (3) ignore = .role=="apply" = fit PARAMETERS on GLSS train rows only; apply
#       rows receive draws but never inform the model (slide "Step 1: Choose
#       a data set to build the model on").
run_mice <- function(frame, target_methods, target_predictors) {
  mice_cols <- setdiff(names(frame), c("hh_key", "household_weight",
                                       "welfare", ".role", collinear_drop))
  mdat <- frame[, mice_cols]
  meth <- make.method(mdat)
  # make.method() also assigns default methods to any shared predictors X that
  # have incidental missing cells. In these prepared teaching files this is a
  # tiny amount of missingness, so mice may fill those X cells while the
  # substantive target remains the missing welfare/NHIS/electricity block.
  for (v in names(target_methods)) meth[v] <- target_methods[v]
  pm <- make.predictorMatrix(mdat)
  for (v in names(target_predictors)) {
    pm[v, ] <- 0
    pm[v, intersect(target_predictors[[v]], colnames(pm))] <- 1
  }
  mice(mdat, m = M, maxit = MAXIT, seed = SYNTH_SEED,
       method = meth, predictorMatrix = pm,
       ignore = frame$.role == "apply", printFlag = FALSE)
}

# This extracts the completed/imputed values from the fitted mice object.
# Pull the apply-row draws out of a fitted mice object, one stacked row per
# (household, imputed dataset). `synth_*` columns hold the IMPUTED values; poverty is
# DERIVED from each drawn welfare here, not drawn.
collect_draws <- function(imp, frame) {
  bind_rows(lapply(seq_len(M), function(i) {
    comp <- complete(imp, i)
    frame %>% select(hh_key, household_weight, .role) %>%
      mutate(.imp = i,
             synth_log_welfare = comp$log_welfare,
             synth_welfare = exp(comp$log_welfare),          # back-transform log -> GHS
             synth_nhis = as.integer(as.character(comp$nhis_any_member_registered)),
             synth_poverty_status = as.character(derive_poverty(exp(comp$log_welfare))),
             synth_poor = as.integer(exp(comp$log_welfare) < POV_ABSOLUTE)) %>%
      filter(.role == "apply") %>% select(-.role)            # keep only the imputed rows
  }))
}

## RUN A: DHS enrichment ---------------------------------------------------
# The real goal: fit on the SAME GLSS train rows, then impute welfare + NHIS into
# the DHS households (whose welfare is missing by design). Each DHS household
# leaves with m drawn welfare values and m derived poverty labels (slides
# "The imputation workflow at a glance" / "Step 2: partially synthetic data").
frame_a <- build_frame(dhs_households, c("log_welfare", "nhis_any_member_registered"))
imp_a <- run_mice(frame_a,
  c(log_welfare = "norm", nhis_any_member_registered = "logreg"),
  list(log_welfare = c(model_pred, "nhis_any_member_registered"),
       nhis_any_member_registered = c(model_pred, "log_welfare")))
draws_a <- collect_draws(imp_a, frame_a)

# This joins each DHS household's imputed welfare/NHIS draws to observed DHS
# descriptors we use for summaries and benchmark comparisons.
dhs_synth <- draws_a %>%
  left_join(dhs_households %>% select(hh_key, region10, urban, wealth_index, wealth_score,
                                      nhis_observed = nhis_any_member_registered),
            by = "hh_key")

# This summarizes the DHS enrichment separately for each imputed dataset.
enrichment_by_imp <- dhs_synth %>% group_by(.imp) %>%
  summarise(synth_welfare_mean_w = round(w_mean(synth_welfare, household_weight), 1),
            synth_welfare_p50 = round(median(synth_welfare, na.rm = TRUE), 1),
            synth_poverty_rate_w = round(100 * w_mean(synth_poor, household_weight), 2),
            synth_nhis_rate_w = round(100 * w_mean(synth_nhis, household_weight), 2),
            observed_nhis_rate_w = round(100 * w_mean(nhis_observed, household_weight), 2),
            .groups = "drop")

# This attaches household-level synthetic poverty to each DHS child record so
# child outcomes can be analyzed by the imputed household poverty status.
dhs_children_synth <- dhs_children %>%
  inner_join(dhs_synth %>% select(hh_key, .imp, synth_poor, synth_poverty_status),
             by = "hh_key", relationship = "many-to-many")

# This estimates the stunting gradient by the three synthetic poverty-status
# groups across imputed datasets, keeping between-imputation variation visible.
gradient <- dhs_children_synth %>%
  group_by(.imp, synth_poverty_status) %>%
  summarise(stunted_rate = 100 * w_mean(stunted, child_weight), .groups = "drop") %>%
  group_by(synth_poverty_status) %>%
  summarise(stunted_rate_pooled = round(mean(stunted_rate), 2),
            between_imp_sd = round(sd(stunted_rate), 2), .groups = "drop")

# This collects the main DHS enrichment summaries for later tables/output.
enrichment_summary <- bind_rows(
  enrichment_by_imp %>% mutate(table = "enrichment_by_imputed_dataset"),
  gradient %>% mutate(table = "stunting_by_synth_poverty_status"))

# This creates a DHS-only wealth-index benchmark for comparison with the
# synthetic poverty gradient.
wealth_benchmark <- dhs_children %>%
  inner_join(dhs_households %>% select(hh_key, wealth_index), by = "hh_key") %>%
  mutate(low_wealth = as.integer(wealth_index <= 2)) %>%
  group_by(low_wealth) %>%
  summarise(stunted_rate = round(100 * w_mean(stunted, child_weight), 2), .groups = "drop")

dhs_overall_stunting <- data.frame(
  group = "All DHS children",
  stunted_rate = round(w_rate(dhs_children$stunted, dhs_children$child_weight), 2),
  between_imp_sd = NA_real_
)

## RUN B: GLSS holdout (Validation Check 1) --------------------------------
# Fit on GLSS train, impute welfare + NHIS into the held-out GLSS rows whose
# TRUE welfare we have hidden. This is the only place we can score imputed
# welfare against ground truth (slide "Validation Check 1 — GLSS holdout").
# Note the chained factorisation (slide "Activity: factor the model"): each
# target conditions on the other (welfare | X, NHIS) and (NHIS | X, welfare).
frame_b <- build_frame(glss_holdout, c("log_welfare", "nhis_any_member_registered"))
imp_b <- run_mice(frame_b,
  c(log_welfare = "norm", nhis_any_member_registered = "logreg"),
  list(log_welfare = c(model_pred, "nhis_any_member_registered"),
       nhis_any_member_registered = c(model_pred, "log_welfare")))
draws_b <- collect_draws(imp_b, frame_b)

# Recover the TRUE holdout welfare we hid, then join imputed-to-true row by row.
# This rebuilds the “answer key” for the GLSS holdout sample.
truth_b <- glss_holdout %>%
  transmute(hh_key, true_welfare = welfare,
            true_poor = as.integer(welfare < POV_ABSOLUTE),
            true_status = as.character(derive_poverty(welfare)),
            true_nhis = nhis_any_member_registered,
            region10, urban, household_weight)

# This joins the synthetic/imputed values to the true holdout values household by household.
val_b <- draws_b %>% inner_join(truth_b, by = "hh_key") %>%
  rename(household_weight = household_weight.x) %>% select(-household_weight.y)
holdout_synth <- val_b

# This calculates validation statistics separately for each imputed dataset.
per_imp <- val_b %>% group_by(.imp) %>%
  summarise(
    synth_welfare_mean_w = w_mean(synth_welfare, household_weight),
    true_welfare_mean_w = w_mean(true_welfare, household_weight),
    synth_poverty_rate_w = 100 * w_mean(synth_poor, household_weight),
    true_poverty_rate_w = 100 * w_mean(true_poor, household_weight),
    mae_log = mean(abs(synth_log_welfare - log(true_welfare)), na.rm = TRUE),
    rmse_log = sqrt(mean((synth_log_welfare - log(true_welfare))^2, na.rm = TRUE)),
    corr_log = cor(synth_log_welfare, log(true_welfare), use = "complete.obs"),
    spearman = cor(synth_welfare, true_welfare, method = "spearman", use = "complete.obs"),
    poverty3_accuracy = mean(synth_poverty_status == true_status, na.rm = TRUE),
    nhis_synth_rate_w = 100 * w_mean(synth_nhis, household_weight),
    nhis_true_rate_w = 100 * w_mean(true_nhis, household_weight),
    nhis_accuracy = mean(synth_nhis == true_nhis, na.rm = TRUE), .groups = "drop")

# This formats the per_imp results into a table for teaching/reporting.
holdout_validation <- bind_rows(
  per_imp %>% mutate(.imp = as.character(.imp)),
  per_imp %>% summarise(across(-.imp, mean)) %>% mutate(.imp = "pooled_mean"),
  per_imp %>% summarise(across(-.imp, sd)) %>% mutate(.imp = "between_imp_sd")
) %>% mutate(across(where(is.numeric), ~ round(.x, 4))) %>% select(.imp, everything())

# This creates a confusion table for poverty status.
holdout_confusion <- val_b %>% count(true_status, synth_poverty_status) %>%
  mutate(n = n / M) %>% arrange(true_status, synth_poverty_status)

# This is a small helper for subgroup validation
# within each imputed dataset and within each group, compare synthetic poverty rates to true poverty rates.
subgrp <- function(dat, gvar) {
  dat %>% group_by(.imp, grp = .data[[gvar]]) %>%
    summarise(synth_pov_w = 100 * w_mean(synth_poor, household_weight),
              true_pov_w = 100 * w_mean(true_poor, household_weight), .groups = "drop") %>%
    group_by(grp) %>%
    summarise(group_var = gvar,
              synth_poverty_rate_w = round(mean(synth_pov_w), 2),
              true_poverty_rate_w = round(mean(true_pov_w), 2),
              gap_pp = round(mean(synth_pov_w - true_pov_w), 2), .groups = "drop")
}
holdout_subgroups <- bind_rows(subgrp(val_b, "region10"), subgrp(val_b, "urban"))

## RUN C: DHS electricity transport check (Validation Check 2) --------------
# The "calibration" check from the literature (slide "Validation Check 2 — transport").
# Electricity is a SHARED variable DHS actually observes. We pretend DHS lacks
# it, predict it from the GLSS-trained model, then compare to the truth DHS
# recorded. It tests whether a GLSS relationship transports to DHS -- on an
# observed target -- WITHOUT needing welfare ground truth.
frame_c <- build_frame(dhs_households, "has_electricity", extra_cols = "has_electricity")
frame_c$log_welfare <- NULL; frame_c$welfare <- NULL
frame_c$nhis_any_member_registered <- NULL
imp_c <- run_mice(frame_c, c(has_electricity = "logreg"),
                  list(has_electricity = model_pred))

# This pulls the imputed DHS electricity draws and joins the true DHS
# electricity value we temporarily hid.
calib <- bind_rows(lapply(seq_len(M), function(i) {
  comp <- complete(imp_c, i)
  frame_c %>% select(hh_key, household_weight, .role, region10) %>%
    mutate(.imp = i, synth_elec = as.integer(as.character(comp$has_electricity))) %>%
    filter(.role == "apply")
})) %>%
  left_join(dhs_households %>% select(hh_key, true_elec = has_electricity, urban), by = "hh_key")

# This calculates the transport-check performance separately for each imputed dataset.
calib_per_imp <- calib %>% group_by(.imp) %>%
  summarise(synth_elec_rate_w = round(100 * w_mean(synth_elec, household_weight), 2),
            true_elec_rate_w = round(100 * w_mean(true_elec, household_weight), 2),
            accuracy = round(mean(synth_elec == true_elec, na.rm = TRUE), 4), .groups = "drop")

# This compares synthetic and true electricity rates within policy-relevant subgroups.
calib_subgrp <- bind_rows(
  calib %>% group_by(grp = as.character(region10)) %>%
    summarise(group_var = "region10",
              synth_rate_w = round(100 * w_mean(synth_elec, household_weight), 2),
              true_rate_w = round(100 * w_mean(true_elec, household_weight), 2), .groups = "drop"),
  calib %>% group_by(grp = as.character(urban)) %>%
    summarise(group_var = "urban",
              synth_rate_w = round(100 * w_mean(synth_elec, household_weight), 2),
              true_rate_w = round(100 * w_mean(true_elec, household_weight), 2), .groups = "drop")
) %>% mutate(gap_pp = round(synth_rate_w - true_rate_w, 2))

# This collects the electricity transport-check summaries for later tables/output.
electricity_calibration <- bind_rows(
  calib_per_imp %>% mutate(table = "by_imputed_dataset", grp = NA, group_var = NA,
                           synth_rate_w = synth_elec_rate_w, true_rate_w = true_elec_rate_w) %>%
    select(table, .imp, group_var, grp, synth_rate_w, true_rate_w, accuracy),
  calib_subgrp %>% mutate(table = "subgroup", .imp = NA, accuracy = NA) %>%
    select(table, .imp, group_var, grp, synth_rate_w, true_rate_w, accuracy, gap_pp))

## model_spec + logged_events ----------------------------------------------
model_spec <- data.frame(
  item = c("data_family", "mice_version", "seed", "m", "maxit",
           "fit_rows_rule", "weights_statement", "welfare_method",
           "welfare_transform", "nhis_method", "electricity_method",
           "poverty_rule", "primary_predictors", "collinear_dropped_from_model",
           "transport_check_predictors", "sensitivity_predictors_used"),
  value = c(DATA_FAMILY, as.character(packageVersion("mice")), SYNTH_SEED, M, MAXIT,
    "mice(ignore=): models fit on GLSS train rows only; holdout/DHS rows receive draws without informing parameters",
    "UNWEIGHTED fitting (mice norm/logreg take no case weights); household_weight used in all summaries",
    "norm (Bayesian linear regression; parameter draws then value draws)",
    "log(welfare); draws back-transformed exp(); positive by construction",
    "logreg (active_sensitivity target; masked in DHS though observed, so the DHS comparison is also a transport diagnostic)",
    "logreg (has_electricity excluded from its own conditioning set; welfare/NHIS not in the transport-check frame)",
    sprintf("derived from drawn welfare at %.2f / %.0f; never drawn directly", POV_EXTREME, POV_ABSOLUTE),
    paste(model_pred, collapse = "; "),
    "members_total, adults_15plus, floor_non_earth: exact linear dependencies; dropped from the MODEL set only, kept in extract/manifest",
    paste(model_pred, collapse = "; "), "none in the primary specification"),
  stringsAsFactors = FALSE)

primary_predictors <- model_spec %>%
  filter(item == "primary_predictors") %>%
  pull(value) %>%
  strsplit("; ", fixed = TRUE) %>%
  unlist()

logged_events <- bind_rows(lapply(
  list(A_enrichment = imp_a, B_holdout = imp_b, C_calibration = imp_c),
  function(imp) {
    le <- imp$loggedEvents
    if (is.null(le)) return(data.frame(n_events = 0L, detail = "none"))
    le %>% count(dep, meth, out, name = "n_events") %>%
      transmute(n_events, detail = paste0(dep, " | ", meth, " | ", out))
  }) %>% setNames(c("A_enrichment", "B_holdout", "C_calibration")), .id = "run")


## ----enrichment-summary-table-------------------------------------------------
enrichment_summary %>%
  filter(table == "enrichment_by_imputed_dataset") %>%
  select(.imp, synth_welfare_mean_w, synth_welfare_p50,
         synth_poverty_rate_w, synth_nhis_rate_w, observed_nhis_rate_w) %>%
  knitr::kable()


## ----enrichment-poverty-plot--------------------------------------------------
enrichment_summary %>%
  filter(table == "enrichment_by_imputed_dataset") %>%
  ggplot(aes(x = factor(.imp), y = synth_poverty_rate_w)) +
  geom_col(fill = "#2f6f73") +
  labs(x = "Imputed dataset", y = "Weighted synthetic poverty rate (%)") +
  theme_minimal(base_size = 12)


## ----derive-not-draw-check----------------------------------------------------
# Proof that poverty is DERIVED, not drawn (slide "From the welfare aggregate
# to poverty"). We re-cut the imputed welfare here and confirm it equals
# the poverty label stored during collect_draws(): mismatches should be zero.
derive_check <- dhs_synth %>%
  mutate(
    derived_status = as.character(cut(
      synth_welfare,
      c(-Inf, POV_EXTREME, POV_ABSOLUTE, Inf),
      labels = c("Very poor", "Poor", "Non poor"))),
    derived_poor = as.integer(synth_welfare < POV_ABSOLUTE)
  ) %>%
  summarise(
    rows = n(),
    status_mismatches = sum(derived_status != synth_poverty_status, na.rm = TRUE),
    poor_mismatches = sum(derived_poor != synth_poor, na.rm = TRUE)
  )

knitr::kable(derive_check)


## ----child-linkage------------------------------------------------------------
child_link_summary <- data.frame(
  rows = nrow(dhs_children_synth),
  imputed_datasets = length(unique(dhs_children_synth$.imp)),
  child_rows_per_imputed_dataset = nrow(dhs_children_synth) / length(unique(dhs_children_synth$.imp)),
  unique_child_ids = length(unique(dhs_children_synth$child_id))
)

knitr::kable(child_link_summary)


## ----stunting-gradient--------------------------------------------------------
poverty_levels <- c("Very poor", "Poor", "Non poor")

stunting_by_imp <- dhs_children_synth %>%
  mutate(synth_poverty_status = factor(synth_poverty_status, levels = poverty_levels)) %>%
  group_by(.imp, synth_poverty_status) %>%
  summarise(stunted_rate = 100 * w_mean(stunted, child_weight), .groups = "drop")

stunting_pooled <- stunting_by_imp %>%
  group_by(synth_poverty_status) %>%
  summarise(between_imp_sd = sd(stunted_rate),
            stunted_rate = mean(stunted_rate), .groups = "drop") %>%
  mutate(group = paste("Synthetic", tolower(as.character(synth_poverty_status))),
         group = gsub("non poor", "non-poor", group, fixed = TRUE),
         across(c(stunted_rate, between_imp_sd), ~ round(.x, 2))) %>%
  select(group, stunted_rate, between_imp_sd)

stunting_display <- bind_rows(dhs_overall_stunting, stunting_pooled)

knitr::kable(stunting_display)


## ----wealth-benchmark---------------------------------------------------------
wealth_benchmark %>%
  mutate(group = ifelse(low_wealth == 1,
                        "DHS wealth bottom two quintiles",
                        "DHS wealth upper three quintiles")) %>%
  select(group, stunted_rate) %>%
  knitr::kable()


## ----child-gradient-plot------------------------------------------------------
overall_stunting_rate <- dhs_overall_stunting$stunted_rate[1]

stunting_pooled %>%
  ggplot(aes(x = group, y = stunted_rate, fill = group)) +
  geom_col(width = 0.65, show.legend = FALSE) +
  geom_hline(yintercept = overall_stunting_rate, linetype = "dashed",
             color = "#262626") +
  annotate("text", x = 2.6, y = overall_stunting_rate + 1,
           label = "Overall DHS rate", size = 3.5, hjust = 0) +
  labs(x = NULL, y = "Weighted stunting rate (%)") +
  theme_minimal(base_size = 12)


## ----rubin-style-pooling------------------------------------------------------
# Step 1: compute the SAME estimate on each imputed dataset separately -- here
# the poor-minus-nonpoor stunting gap, plus its within-imputation variance.
gap_by_imp <- bind_rows(lapply(split(dhs_children_synth, dhs_children_synth$.imp), function(dat) {
  poor <- dat %>% filter(synth_poor == 1)
  nonpoor <- dat %>% filter(synth_poor == 0)
  poor_est <- weighted_binary_est(poor$stunted, poor$child_weight)
  nonpoor_est <- weighted_binary_est(nonpoor$stunted, nonpoor$child_weight)
  data.frame(.imp = unique(dat$.imp),
             gap_pp = 100 * (poor_est$estimate - nonpoor_est$estimate),
             within_var_pp2 = 100^2 * (poor_est$var + nonpoor_est$var))
}))

# Step 2: combine the m estimates with Rubin's rules. The reported SE now
# carries BOTH the usual sampling noise AND the extra spread from imputing
# welfare (slide "Multiple imputation keeps uncertainty visible").
pooled_gap <- pool_scalar(gap_by_imp$gap_pp, gap_by_imp$within_var_pp2) %>%
  mutate(across(everything(), ~ round(.x, 3)))

knitr::kable(gap_by_imp %>% mutate(across(where(is.numeric), ~ round(.x, 3))))
knitr::kable(pooled_gap)


## ----holdout-summary----------------------------------------------------------
# One row per imputed dataset plus pooled mean and between-imputation SD.
# Read across a row: imputed poverty rate should track the true rate.
knitr::kable(holdout_validation)


## ----holdout-poverty-plot-----------------------------------------------------
holdout_plot <- holdout_validation %>%
  filter(.imp != "between_imp_sd") %>%
  mutate(.imp = factor(.imp, levels = c(as.character(seq_len(M)), "pooled_mean"))) %>%
  select(.imp, synth_poverty_rate_w, true_poverty_rate_w) %>%
  tidyr::pivot_longer(-.imp, names_to = "series", values_to = "poverty_rate")

ggplot(holdout_plot, aes(x = .imp, y = poverty_rate, color = series, group = series)) +
  geom_point(size = 2.2) +
  geom_line() +
  labs(x = "Imputed dataset", y = "Weighted poverty rate (%)", color = NULL) +
  theme_minimal(base_size = 12)


## ----holdout-density-overlay--------------------------------------------------
truth_density <- holdout_synth %>%
  distinct(hh_key, true_welfare) %>%
  mutate(log_welfare = log(true_welfare), series = "True holdout welfare")

synth_density <- holdout_synth %>%
  mutate(log_welfare = synth_log_welfare,
         series = paste("Synthetic dataset", .imp))

ggplot() +
  geom_density(data = synth_density, aes(x = log_welfare, group = .imp),
               color = "#2f6f73", alpha = 0.28, linewidth = 0.8) +
  geom_density(data = truth_density, aes(x = log_welfare),
               color = "#262626", linewidth = 1.2) +
  labs(x = "Log welfare", y = "Density") +
  theme_minimal(base_size = 12)


## ----holdout-confusion--------------------------------------------------------
holdout_confusion %>%
  tidyr::pivot_wider(names_from = synth_poverty_status,
                     values_from = n,
                     values_fill = 0) %>%
  knitr::kable()


## ----holdout-subgroups--------------------------------------------------------
holdout_subgroups %>%
  mutate(across(c(synth_poverty_rate_w, true_poverty_rate_w, gap_pp),
                ~ round(.x, 1))) %>%
  arrange(group_var, grp) %>%
  knitr::kable()


## ----transport-check----------------------------------------------------------
electricity_calibration %>%
  filter(table == "by_imputed_dataset") %>%
  select(.imp, synth_rate_w, true_rate_w, accuracy) %>%
  knitr::kable()


## ----transport-subgroups------------------------------------------------------
electricity_calibration %>%
  filter(table == "subgroup", group_var %in% c("region10", "urban")) %>%
  mutate(gap_pp = round(synth_rate_w - true_rate_w, 1)) %>%
  arrange(group_var, grp) %>%
  knitr::kable()


## ----extension-engine-switch, eval=FALSE--------------------------------------
# engine <- "pmm"
# allowed_engines <- c("norm", "pmm", "cart", "rf")
# if (!engine %in% allowed_engines) {
#   stop("Choose one of: ", paste(allowed_engines, collapse = ", "))
# }
# 
# run_engine_holdout <- function(engine, n_train = 1500, n_holdout = 500,
#                                m = 2, maxit = 2) {
#   set.seed(EXTENSION_SEED)
#   use_cols <- c("hh_key", "household_weight", primary_predictors, "welfare")
# 
#   tr_pool <- glss_train %>%
#     select(all_of(use_cols)) %>%
#     filter(if_all(all_of(c(primary_predictors, "welfare")), ~ !is.na(.x))) %>%
#     arrange(hh_key)
#   ho_pool <- glss_holdout %>%
#     select(all_of(use_cols)) %>%
#     filter(if_all(all_of(c(primary_predictors, "welfare")), ~ !is.na(.x))) %>%
#     arrange(hh_key)
# 
#   tr <- tr_pool %>% slice_sample(n = min(n_train, nrow(tr_pool))) %>% mutate(.role = "train")
#   ho <- ho_pool %>% slice_sample(n = min(n_holdout, nrow(ho_pool))) %>% mutate(.role = "holdout")
# 
#   stacked <- bind_rows(tr, ho) %>%
#     mutate(log_welfare = ifelse(.role == "train", log(welfare), NA_real_))
#   for (v in intersect(primary_predictors, names(stacked)))
#     if (is.character(stacked[[v]])) stacked[[v]] <- factor(stacked[[v]])
#   if ("region10" %in% names(stacked)) stacked$region10 <- factor(stacked$region10)
# 
#   mdat <- stacked %>% select(all_of(c(primary_predictors, "log_welfare")))
#   meth <- mice::make.method(mdat); meth[] <- ""; meth["log_welfare"] <- engine
#   pm <- mice::make.predictorMatrix(mdat); pm[, ] <- 0
#   pm["log_welfare", primary_predictors] <- 1
# 
#   elapsed <- system.time({
#     imp <- mice::mice(mdat, m = m, maxit = maxit, method = meth, predictorMatrix = pm,
#                       ignore = stacked$.role == "holdout", seed = EXTENSION_SEED, printFlag = FALSE)
#   })
# 
#   draws <- bind_rows(lapply(seq_len(m), function(i) {
#     comp <- mice::complete(imp, i)
#     holdout_idx <- stacked$.role == "holdout"
#     stacked %>% filter(.role == "holdout") %>%
#       transmute(hh_key, household_weight, .imp = i,
#                 synth_log_welfare = comp$log_welfare[holdout_idx],
#                 synth_welfare = exp(synth_log_welfare),
#                 synth_poor = as.integer(synth_welfare < POV_ABSOLUTE),
#                 true_welfare = welfare, true_poor = as.integer(welfare < POV_ABSOLUTE))
#   }))
# 
#   recovery_metrics(draws, engine) %>%
#     mutate(train_rows = nrow(tr), holdout_rows = nrow(ho),
#            runtime_sec = round(elapsed[["elapsed"]], 1))
# }
# 
# extension_results <- bind_rows(
#   run_engine_holdout("norm"),
#   if (engine == "norm") NULL else run_engine_holdout(engine)
# ) %>%
#   mutate(across(c(mae_log, rmse_log, corr_log,
#                   synth_poverty_rate_w, true_poverty_rate_w), ~ round(.x, 3)))
# 
# knitr::kable(extension_results)


## ----manifest-roles-----------------------------------------------------------
role_counts <- manifest %>%
  count(manifest_role, sort = TRUE)

knitr::kable(role_counts)


## ----model-spec---------------------------------------------------------------
model_table <- data.frame(
  design_choice = c("Fitting rows", "Weights", "Welfare target",
                    "NHIS target", "Poverty status", "Primary predictors"),
  implementation = c(
    model_spec$value[model_spec$item == "fit_rows_rule"],
    model_spec$value[model_spec$item == "weights_statement"],
    paste(model_spec$value[model_spec$item == "welfare_method"],
          model_spec$value[model_spec$item == "welfare_transform"], sep = "; "),
    model_spec$value[model_spec$item == "nhis_method"],
    model_spec$value[model_spec$item == "poverty_rule"],
    paste(primary_predictors, collapse = ", ")
  )
)

knitr::kable(model_table)


## ----model-drops--------------------------------------------------------------
dropped <- model_spec %>%
  filter(item == "collinear_dropped_from_model") %>%
  pull(value)

dropped

