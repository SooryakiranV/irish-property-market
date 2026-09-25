from pathlib import Path

import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_RPPI_DIR = PROJECT_ROOT / "data" / "raw" / "rppi"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = PROCESSED_DATA_DIR / "rppi_cleaned.csv"


# ============================================================
# Expected columns
# ============================================================

EXPECTED_COLUMNS = [
    "Statistic Label",
    "Month",
    "Type of Residential Property",
    "UNIT",
    "VALUE",
]


# ============================================================
# Load RPPI data
# ============================================================

def load_rppi_data() -> pd.DataFrame:
    """Load the downloaded CSO RPPI CSV file."""

    csv_files = list(RAW_RPPI_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No RPPI CSV file found in: {RAW_RPPI_DIR}"
        )

    if len(csv_files) > 1:
        raise ValueError(
            f"Expected one RPPI CSV file, but found {len(csv_files)}: "
            f"{csv_files}"
        )

    input_file = csv_files[0]

    print(f"Loading RPPI file: {input_file.name}")

    df = pd.read_csv(
        input_file,
        encoding="utf-8",
        low_memory=False,
    )

    return df


# ============================================================
# Validate structure
# ============================================================

def validate_structure(df: pd.DataFrame) -> None:
    """Validate the downloaded RPPI structure."""

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {missing_columns}"
        )

    print("RPPI structure validation passed.")


# ============================================================
# Clean and transform RPPI data
# ============================================================

def clean_rppi_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform the RPPI dataset."""

    df = df.copy()

    # --------------------------------------------------------
    # Remove exact duplicates
    # --------------------------------------------------------

    rows_before = len(df)

    df = df.drop_duplicates().copy()

    rows_after = len(df)

    print(f"Rows before duplicate removal: {rows_before:,}")
    print(f"Rows after duplicate removal: {rows_after:,}")
    print(f"Duplicates removed: {rows_before - rows_after:,}")

    # --------------------------------------------------------
    # Clean text columns
    # --------------------------------------------------------

    text_columns = [
        "Statistic Label",
        "Month",
        "Type of Residential Property",
        "UNIT",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # Convert month to datetime
    # --------------------------------------------------------

    df["month"] = pd.to_datetime(
        df["Month"],
        format="%Y %B",
        errors="coerce",
    )

    # --------------------------------------------------------
    # Convert RPPI value to numeric
    # --------------------------------------------------------

    df["rppi_value"] = pd.to_numeric(
        df["VALUE"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Create time dimensions
    # --------------------------------------------------------

    df["year"] = df["month"].dt.year.astype("Int32")

    df["month_number"] = (
        df["month"]
        .dt.month
        .astype("Int32")
    )

    df["quarter"] = (
        df["month"]
        .dt.quarter
        .astype("Int32")
    )

    df["year_month"] = (
        df["month"]
        .dt.to_period("M")
        .astype("string")
    )

    # --------------------------------------------------------
    # Rename geographic/property series
    # --------------------------------------------------------

    df["property_series"] = (
        df["Type of Residential Property"]
        .astype("string")
    )

    # --------------------------------------------------------
    # Remove rows without a valid month
    # --------------------------------------------------------

    invalid_dates = df["month"].isna().sum()

    print(f"Invalid RPPI dates: {invalid_dates:,}")

    if invalid_dates > 0:
        raise ValueError(
            "Invalid RPPI dates detected. "
            "Check the Month column before continuing."
        )

    # --------------------------------------------------------
    # Remove rows without an RPPI value
    # --------------------------------------------------------

    missing_values = df["rppi_value"].isna().sum()

    print(f"Missing RPPI values: {missing_values:,}")

    # Missing VALUE rows are legitimate in some CSO series,
    # so they are retained for now.

    # --------------------------------------------------------
    # Select final columns
    # --------------------------------------------------------

    df = df[
        [
            "Statistic Label",
            "Month",
            "Type of Residential Property",
            "UNIT",
            "VALUE",
            "month",
            "year",
            "month_number",
            "quarter",
            "year_month",
            "property_series",
            "rppi_value",
        ]
    ]

    return df


# ============================================================
# Summary
# ============================================================

def print_summary(df: pd.DataFrame) -> None:
    """Print summary information about the cleaned RPPI data."""

    print("\n" + "=" * 60)
    print("RPPI DATASET SUMMARY")
    print("=" * 60)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print(
        f"Date range: "
        f"{df['month'].min().date()} "
        f"to "
        f"{df['month'].max().date()}"
    )

    print("\nProperty/geographic series:")

    print(
        df["property_series"]
        .value_counts()
        .to_string()
    )

    print("\nUnits:")

    print(
        df["UNIT"]
        .value_counts()
        .to_string()
    )

    print("\nMissing values:")

    missing = (
        df.isna()
        .sum()
        .sort_values(ascending=False)
    )

    print(missing.to_string())


# ============================================================
# Save processed data
# ============================================================

def save_processed_data(df: pd.DataFrame) -> None:
    """Save the cleaned RPPI dataset."""

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print("\nProcessed RPPI dataset saved to:")
    print(OUTPUT_FILE)

    print(f"Saved rows: {len(df):,}")
    print(f"Saved columns: {len(df.columns)}")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    df = load_rppi_data()

    validate_structure(df)

    df = clean_rppi_data(df)

    print_summary(df)

    save_processed_data(df)

    print("\n" + "=" * 60)
    print("RPPI INGESTION COMPLETED SUCCESSFULLY")
    print("=" * 60)