from pathlib import Path

import pandas as pd


SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def list_tabular_files(raw_dir: str | Path) -> list[Path]:
    """Return supported tabular files from the raw data directory."""
    raw_path = Path(raw_dir)
    return sorted(
        path
        for path in raw_path.glob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def load_table(path: str | Path) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path)

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)

    raise ValueError(f"Unsupported file type: {file_path.suffix}")


def load_raw_tables(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load all supported tabular files in raw_dir."""
    tables = {}

    for file_path in list_tabular_files(raw_dir):
        tables[file_path.stem] = load_table(file_path)

    return tables
