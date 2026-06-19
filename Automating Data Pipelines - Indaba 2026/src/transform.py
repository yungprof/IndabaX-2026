import pandas as pd


def clean_text(value):
    if pd.isna(value):
        return value
    return str(value).strip().lower().replace("_", " ")


def clean_column_name(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


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


def standardize_treatment(value):
    value = clean_text(value)

    if value in {"control", "open sun", "open-sun", "no pv", "no panels"}:
        return "open_sun_control"

    if value in {"agrivoltaic", "raised pv", "under pv", "under panels", "solar pv"}:
        return "agrivoltaic"

    if value in {"ground mounted pv", "ground-mounted pv", "bare land pv"}:
        return "ground_mounted_pv"

    return value


def rename_with_contract(
    df: pd.DataFrame,
    column_map: dict[str, str],
) -> pd.DataFrame:
    rename_map = {
        raw_column: standard_column
        for standard_column, raw_column in column_map.items()
        if raw_column in df.columns
    }

    renamed = df.rename(columns=rename_map).copy()
    renamed.columns = [clean_column_name(column) for column in renamed.columns]
    return renamed


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


def summarize_crop_performance(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = ["crop", "treatment", "yield_value"]
    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Cannot summarize crop performance. Missing columns: {missing}")

    return (
        df.dropna(subset=["crop", "treatment", "yield_value"])
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


def compare_treatments(summary: pd.DataFrame) -> pd.DataFrame:
    comparison = (
        summary.pivot(index="crop", columns="treatment", values="mean_yield")
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


def summarize_energy(df: pd.DataFrame) -> pd.DataFrame:
    if "energy_value" not in df.columns:
        raise ValueError("Cannot summarize energy data. Missing column: energy_value")

    group_columns = ["treatment"]
    if "plot" in df.columns:
        group_columns = ["plot", "treatment"]

    return (
        df.dropna(subset=["energy_value"])
        .groupby(group_columns, dropna=False)
        .agg(
            observations=("energy_value", "count"),
            mean_energy=("energy_value", "mean"),
            total_energy=("energy_value", "sum"),
        )
        .reset_index()
    )
