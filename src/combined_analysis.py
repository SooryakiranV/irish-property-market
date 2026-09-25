from pathlib import Path

import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PPR_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ppr_cleaned.csv"
)

RPPI_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rppi_cleaned.csv"
)


# ============================================================
# Load PPR dataset
# ============================================================

def load_ppr_data() -> pd.DataFrame:
    """Load the processed PPR transaction dataset."""

    if not PPR_FILE.exists():
        raise FileNotFoundError(
            f"PPR dataset not found: {PPR_FILE}"
        )

    print("Loading PPR dataset...")

    df = pd.read_csv(
        PPR_FILE,
        encoding="utf-8",
        low_memory=False,
    )

    df["sale_date"] = pd.to_datetime(
        df["sale_date"],
        errors="coerce",
    )

    df["sale_year_month"] = (
        df["sale_date"]
        .dt.to_period("M")
    )

    print(f"PPR rows loaded: {len(df):,}")

    return df


# ============================================================
# Load RPPI dataset
# ============================================================

def load_rppi_data() -> pd.DataFrame:
    """Load the processed CSO RPPI dataset."""

    if not RPPI_FILE.exists():
        raise FileNotFoundError(
            f"RPPI dataset not found: {RPPI_FILE}"
        )

    print("Loading RPPI dataset...")

    df = pd.read_csv(
        RPPI_FILE,
        encoding="utf-8",
        low_memory=False,
    )

    df["Month"] = pd.to_datetime(
        df["Month"],
        errors="coerce",
    )

    df["year_month"] = (
        df["Month"]
        .dt.to_period("M")
    )

    print(f"RPPI rows loaded: {len(df):,}")

    return df


# ============================================================
# Validate PPR dataset
# ============================================================

def validate_ppr(df: pd.DataFrame) -> None:
    """Validate the PPR dataset before analysis."""

    required_columns = [
        "sale_date",
        "sale_year_month",
        "county",
        "price_eur",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"PPR dataset is missing columns: {missing}"
        )

    if df["sale_date"].isna().any():
        raise ValueError(
            "PPR dataset contains invalid sale dates."
        )

    print("PPR validation passed.")


# ============================================================
# Validate RPPI dataset
# ============================================================

def validate_rppi(df: pd.DataFrame) -> None:
    """Validate the RPPI dataset before analysis."""

    required_columns = [
        "Month",
        "year_month",
        "property_series",
        "rppi_value",
        "UNIT",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"RPPI dataset is missing columns: {missing}"
        )

    if df["Month"].isna().any():
        raise ValueError(
            "RPPI dataset contains invalid dates."
        )

    print("RPPI validation passed.")


# ============================================================
# PPR monthly analysis
# ============================================================

def create_ppr_monthly_analysis(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate PPR transactions by month.
    """

    monthly = (
        df.groupby("sale_year_month")
        .agg(
            transactions=("price_eur", "size"),
            total_value=("price_eur", "sum"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
    )

    monthly = monthly.rename(
        columns={
            "sale_year_month": "year_month",
        }
    )

    return monthly


# ============================================================
# RPPI national analysis
# ============================================================

def create_national_rppi_analysis(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract the national all-residential-property
    RPPI series.
    """

    national = df[
        (
            df["property_series"]
            == "National - all residential properties"
        )
        & (
            df["UNIT"]
            == "Base 2015=100"
        )
    ].copy()

    national = national[
        [
            "year_month",
            "rppi_value",
        ]
    ]

    national = national.rename(
        columns={
            "rppi_value": "national_rppi",
        }
    )

    return national


# ============================================================
# Combine PPR and RPPI
# ============================================================

def create_combined_dataset(
    ppr_monthly: pd.DataFrame,
    national_rppi: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine monthly PPR transaction statistics
    with the national RPPI.
    """

    combined = pd.merge(
        ppr_monthly,
        national_rppi,
        on="year_month",
        how="left",
    )

    combined = combined.sort_values(
        "year_month"
    ).reset_index(drop=True)

    return combined


# ============================================================
# Combined dataset summary
# ============================================================

def print_combined_summary(
    combined: pd.DataFrame,
) -> None:
    """Display summary information for the combined dataset."""

    print("\n" + "=" * 60)
    print("COMBINED PPR + RPPI DATASET")
    print("=" * 60)

    print(
        f"Monthly observations: "
        f"{len(combined):,}"
    )

    print(
        f"Date range: "
        f"{combined['year_month'].min()} "
        f"to "
        f"{combined['year_month'].max()}"
    )

    print(
        f"Missing national RPPI values: "
        f"{combined['national_rppi'].isna().sum():,}"
    )

    print("\nFirst 10 combined observations:")

    print(
        combined.head(10).to_string(
            index=False
        )
    )


# ============================================================
# Main execution
# ============================================================

if __name__ == "__main__":

    print("Starting combined property market analysis...")

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    ppr = load_ppr_data()
    rppi = load_rppi_data()

    # --------------------------------------------------------
    # Validate datasets
    # --------------------------------------------------------

    validate_ppr(ppr)
    validate_rppi(rppi)

    # --------------------------------------------------------
    # Create monthly PPR analysis
    # --------------------------------------------------------

    ppr_monthly = create_ppr_monthly_analysis(
        ppr
    )

    print(
        f"PPR monthly observations: "
        f"{len(ppr_monthly):,}"
    )

    # --------------------------------------------------------
    # Extract national RPPI
    # --------------------------------------------------------

    national_rppi = create_national_rppi_analysis(
        rppi
    )

    print(
        f"National RPPI observations: "
        f"{len(national_rppi):,}"
    )

    # --------------------------------------------------------
    # Combine datasets
    # --------------------------------------------------------

    combined = create_combined_dataset(
        ppr_monthly,
        national_rppi,
    )

    # --------------------------------------------------------
# Save combined dataset
# --------------------------------------------------------

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "combined"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "ppr_rppi_combined.csv"
)

combined.to_csv(
    OUTPUT_FILE,
    index=False,
)

# --------------------------------------------------------
# Display summary
# --------------------------------------------------------

print_combined_summary(
    combined
)

print(
    f"\nCombined dataset saved to:"
    f"\n{OUTPUT_FILE}"
)

print(
    f"Saved rows: {len(combined):,}"
)

print(
    f"Saved columns: {len(combined.columns)}"
)

print("\n" + "=" * 60)
print("COMBINED ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 60)