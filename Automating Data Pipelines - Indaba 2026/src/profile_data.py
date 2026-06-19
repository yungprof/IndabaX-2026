from pathlib import Path

import pandas as pd


def profile_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a compact data profile for one DataFrame."""
    return pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(df[column].dtype) for column in df.columns],
            "missing_count": [int(df[column].isna().sum()) for column in df.columns],
            "missing_pct": [
                round(float(df[column].isna().mean() * 100), 2)
                for column in df.columns
            ],
            "unique_values": [
                int(df[column].nunique(dropna=True)) for column in df.columns
            ],
        }
    )


def profile_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Profile every loaded table."""
    return {name: profile_table(df) for name, df in tables.items()}


def save_profiles(
    profiles: dict[str, pd.DataFrame],
    reports_dir: str | Path,
) -> None:
    """Save profiling reports as CSV files."""
    output_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, profile in profiles.items():
        profile.to_csv(output_dir / f"profile_{name}.csv", index=False)
