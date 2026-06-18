# Shared path helpers for the IndabaX Ghana 2026 workshop pipeline.
#
# Scripts can be run from the project root or from a subfolder. The helpers
# below find the repository root by looking for files that should exist at the
# top of both the private working repo and the public teaching repo.

project_root <- function() {
  current <- normalizePath(getwd(), mustWork = TRUE)

  repeat {
    has_project_files <- (
      file.exists(file.path(current, "slides-indabax-theory.Rmd")) ||
        file.exists(file.path(current, "practical-indabax-synthesis-live-compute.Rmd")) ||
        file.exists(file.path(current, "part2-synthetic-data-tutorial-practical-indabax-2026.Rmd"))
    ) &&
      file.exists(file.path(current, "code", "utils", "project_paths.R"))

    if (has_project_files) {
      return(current)
    }

    parent <- dirname(current)
    if (identical(parent, current)) {
      stop("Could not find project root. Run from inside ACET-workshop-gdss-2026.")
    }

    current <- parent
  }
}

project_path <- function(...) {
  file.path(project_root(), ...)
}

ensure_dir <- function(path) {
  dir.create(path, showWarnings = FALSE, recursive = TRUE)
  invisible(path)
}

ensure_project_dirs <- function() {
  dirs <- c(
    "data/dhs2014/processed",
    "data/glss6/processed",
    "data/bridge/processed",
    "output/diagnostics",
    "output/logs",
    "output/figures"
  )

  invisible(lapply(project_path(dirs), ensure_dir))
}
