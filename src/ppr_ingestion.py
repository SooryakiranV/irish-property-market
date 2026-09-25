from pathlib import Path

import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

PPR_FILE = RAW_DATA_DIR / "PPR-ALL.csv"


# ============================================================
# Load data
# ============================================================

def load_ppr_data() -> pd.DataFrame:
    """
    Load the Residential Property Price Register (PPR) CSV.

    Returns
    -------
    pandas.DataFrame
        Raw PPR transaction data.
    """

    if not PPR_FILE.exists():
        raise FileNotFoundError(
            f"PPR file not found: {PPR_FILE}"
        )

    df = pd.read_csv(
        PPR_FILE,
        encoding="cp1252",
        low_memory=False,
    )

    return df


# ============================================================
# Structural validation
# ============================================================

def validate_ppr_structure(df: pd.DataFrame) -> None:
    """
    Validate that the PPR dataset contains the expected columns.
    """

    expected_columns = [
        "Date of Sale (dd/mm/yyyy)",
        "Address",
        "County",
        "Eircode",
        "Price (€)",
        "Not Full Market Price",
        "VAT Exclusive",
        "Description of Property",
        "Property Size Description",
    ]

    missing_columns = [
        column
        for column in expected_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {missing_columns}"
        )

    print("PPR structure validation passed.")


# ============================================================
# Missing-value validation
# ============================================================

def validate_missing_values(df: pd.DataFrame) -> None:
    """
    Report missing values in each PPR column.
    """

    missing_values = df.isna().sum()

    print("\nMissing values:")

    for column, count in missing_values.items():
        print(f"- {column}: {count:,}")


# ============================================================
# Duplicate validation
# ============================================================

def validate_duplicates(df: pd.DataFrame) -> None:
    """
    Check for completely duplicated rows in the PPR dataset.
    """

    duplicate_count = df.duplicated().sum()

    print(f"\nDuplicate rows: {duplicate_count:,}")


def inspect_duplicates(df: pd.DataFrame) -> None:
    """
    Display a small sample of completely duplicated rows.
    """

    duplicates = df[df.duplicated(keep=False)]

    print("\nSample duplicated rows:")

    if duplicates.empty:
        print("No duplicated rows found.")
    else:
        print(
            duplicates
            .head(10)
            .to_string(index=False)
        )


def validate_duplicate_records(df: pd.DataFrame) -> None:
    """
    Check how many rows remain after removing exact duplicate records.
    """

    unique_df = df.drop_duplicates()

    removed_count = len(df) - len(unique_df)

    print(
        f"\nRows before removing exact duplicates: "
        f"{len(df):,}"
    )

    print(
        f"Rows after removing exact duplicates: "
        f"{len(unique_df):,}"
    )

    print(
        f"Exact duplicate rows identified: "
        f"{removed_count:,}"
    )


# ============================================================
# Date validation
# ============================================================

def validate_sale_dates(df: pd.DataFrame) -> None:
    """
    Validate the PPR sale date column.
    """

    date_column = "Date of Sale (dd/mm/yyyy)"

    parsed_dates = pd.to_datetime(
        df[date_column],
        format="%d/%m/%Y",
        errors="coerce",
    )

    invalid_dates = parsed_dates.isna().sum()

    print(
        f"\nInvalid sale dates: "
        f"{invalid_dates:,}"
    )

    if invalid_dates > 0:
        print(
            "Warning: Some sale dates could not be parsed."
        )
    else:
        print("Sale date validation passed.")


# ============================================================
# Price validation
# ============================================================

def validate_prices(df: pd.DataFrame) -> None:
    """
    Validate that all PPR prices can be converted
    to numeric values.
    """

    price_column = "Price (€)"

    cleaned_prices = (
        df[price_column]
        .astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    numeric_prices = pd.to_numeric(
        cleaned_prices,
        errors="coerce",
    )

    invalid_prices = numeric_prices.isna().sum()

    print(
        f"\nInvalid prices: "
        f"{invalid_prices:,}"
    )

    if invalid_prices > 0:
        print(
            "Warning: Some prices could not be "
            "converted to numeric values."
        )
    else:
        print("Price validation passed.")


# ============================================================
# County inspection
# ============================================================

def inspect_counties(df: pd.DataFrame) -> None:
    """
    Inspect the county values present in the PPR dataset.
    """

    county_counts = df["County"].value_counts(
        dropna=False
    )

    print("\nCounty values:")
    print(county_counts.to_string())


# ============================================================
# Price inspection
# ============================================================

def inspect_price_range(df: pd.DataFrame) -> None:
    """
    Inspect the minimum and maximum property prices.
    """

    price_column = "price_eur"

    print("\nPrice range:")
    print(
        f"Minimum price: "
        f"€{df[price_column].min():,.2f}"
    )
    print(
        f"Maximum price: "
        f"€{df[price_column].max():,.2f}"
    )


def inspect_highest_prices(df: pd.DataFrame) -> None:
    """
    Display the 10 highest-priced PPR transactions.
    """

    highest_prices = (
        df.nlargest(10, "price_eur")
        [
            [
                "sale_date",
                "address",
                "county",
                "price_eur",
                "not_full_market_price",
                "vat_exclusive",
                "property_description",
            ]
        ]
    )

    print("\n10 highest-priced transactions:")
    print(
        highest_prices.to_string(index=False)
    )


# ============================================================
# Property classification inspection
# ============================================================

def inspect_property_classification(
    df: pd.DataFrame,
) -> None:
    """
    Display property classification counts.
    """

    new_count = int(
        df["is_new_property"].sum()
    )

    second_hand_count = int(
        df["is_second_hand_property"].sum()
    )

    neither_count = int(
        (
            ~df["is_new_property"]
            & ~df["is_second_hand_property"]
        ).sum()
    )

    both_count = int(
        (
            df["is_new_property"]
            & df["is_second_hand_property"]
        ).sum()
    )

    print("\nProperty classification summary:")
    print(
        f"New properties: {new_count:,}"
    )
    print(
        f"Second-hand properties: "
        f"{second_hand_count:,}"
    )
    print(
        f"Neither classification: "
        f"{neither_count:,}"
    )
    print(
        f"Both classifications: "
        f"{both_count:,}"
    )


# ============================================================
# Data cleaning and transformation
# ============================================================

def clean_ppr_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and transform the PPR dataset into
    an analysis-ready DataFrame.

    Transformations:
    - Remove exact duplicate records
    - Convert sale date to datetime
    - Convert price from currency text to numeric
    - Standardise column names
    - Standardise categorical values
    - Create date-based features
    - Create transaction-type flags
    - Extract property size category
    """

    cleaned_df = df.drop_duplicates().copy()

    removed_count = (
        len(df) - len(cleaned_df)
    )

    # --------------------------------------------------------
    # Clean sale date
    # --------------------------------------------------------

    cleaned_df[
        "Date of Sale (dd/mm/yyyy)"
    ] = pd.to_datetime(
        cleaned_df[
            "Date of Sale (dd/mm/yyyy)"
        ],
        format="%d/%m/%Y",
        errors="coerce",
    )

    # --------------------------------------------------------
    # Clean price
    # --------------------------------------------------------

    cleaned_df["Price (€)"] = (
        cleaned_df["Price (€)"]
        .astype(str)
        .str.replace(
            "€",
            "",
            regex=False,
        )
        .str.replace(
            ",",
            "",
            regex=False,
        )
        .str.strip()
    )

    cleaned_df["Price (€)"] = (
        pd.to_numeric(
            cleaned_df["Price (€)"],
            errors="coerce",
        )
    )

    # --------------------------------------------------------
    # Standardise text columns
    # --------------------------------------------------------

    text_columns = [
        "Address",
        "County",
        "Eircode",
        "Not Full Market Price",
        "VAT Exclusive",
        "Description of Property",
        "Property Size Description",
    ]

    for column in text_columns:
        cleaned_df[column] = (
            cleaned_df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # Standardise county names
    # --------------------------------------------------------

    cleaned_df["County"] = (
        cleaned_df["County"]
        .str.title()
    )

    # --------------------------------------------------------
    # Standardise Yes / No fields
    # --------------------------------------------------------

    yes_no_columns = [
        "Not Full Market Price",
        "VAT Exclusive",
    ]

    for column in yes_no_columns:
        cleaned_df[column] = (
            cleaned_df[column]
            .str.title()
        )

    # --------------------------------------------------------
    # Create date features
    # --------------------------------------------------------

    cleaned_df["sale_year"] = (
        cleaned_df[
            "Date of Sale (dd/mm/yyyy)"
        ].dt.year
    )

    cleaned_df["sale_month"] = (
        cleaned_df[
            "Date of Sale (dd/mm/yyyy)"
        ].dt.month
    )

    cleaned_df["sale_quarter"] = (
        cleaned_df[
            "Date of Sale (dd/mm/yyyy)"
        ].dt.quarter
    )

    cleaned_df["sale_year_month"] = (
        cleaned_df[
            "Date of Sale (dd/mm/yyyy)"
        ]
        .dt.to_period("M")
        .astype("string")
    )

    # --------------------------------------------------------
    # Create transaction flags
    # --------------------------------------------------------

    cleaned_df["is_not_full_market_price"] = (
        cleaned_df["Not Full Market Price"]
        .eq("Yes")
    )

    cleaned_df["is_vat_exclusive"] = (
        cleaned_df["VAT Exclusive"]
        .eq("Yes")
    )

    # --------------------------------------------------------
    # Create property type flags
    #
    # The PPR data contains descriptions such as:
    # "New Dwelling house /Apartment"
    # "Second-Hand Dwelling house /Apartment"
    #
    # We therefore classify based on the actual
    # description wording in the dataset.
    # --------------------------------------------------------

    property_description = (
        cleaned_df[
            "Description of Property"
        ]
        .astype("string")
        .str.lower()
        .str.strip()
    )

    cleaned_df["is_new_property"] = (
        property_description
        .str.contains(
            "new dwelling",
            na=False,
        )
    )

    cleaned_df["is_second_hand_property"] = (
        property_description
        .str.contains(
            "second-hand",
            na=False,
        )
    )

    # --------------------------------------------------------
    # Extract property size category
    # --------------------------------------------------------

    size_description = (
        cleaned_df[
            "Property Size Description"
        ]
        .fillna("")
        .astype("string")
        .str.lower()
    )

    cleaned_df[
        "property_size_category"
    ] = "Unknown"

    cleaned_df.loc[
        size_description.str.contains(
            "less than 38",
            na=False,
        ),
        "property_size_category",
    ] = "Under 38 sq m"

    cleaned_df.loc[
        (
            size_description.str.contains(
                "greater than or equal to 38",
                na=False,
            )
            |
            size_description.str.contains(
                "greater than orequal to 38",
                na=False,
            )
        )
        &
        size_description.str.contains(
            "less than 125",
            na=False,
        ),
        "property_size_category",
    ] = "38-124 sq m"

    cleaned_df.loc[
        (
            size_description.str.contains(
                "greater than or equal to 125",
                na=False,
            )
            |
            size_description.str.contains(
                "greater than orequal to 125",
                na=False,
            )
        ),
        "property_size_category",
    ] = "125 sq m or more"

    # --------------------------------------------------------
    # Standardise column names
    # --------------------------------------------------------

    cleaned_df = cleaned_df.rename(
        columns={
            "Date of Sale (dd/mm/yyyy)": "sale_date",
            "Address": "address",
            "County": "county",
            "Eircode": "eircode",
            "Price (€)": "price_eur",
            "Not Full Market Price":
                "not_full_market_price",
            "VAT Exclusive":
                "vat_exclusive",
            "Description of Property":
                "property_description",
            "Property Size Description":
                "property_size_description",
        }
    )

    # --------------------------------------------------------
    # Final column ordering
    # --------------------------------------------------------

    cleaned_df = cleaned_df[
        [
            "sale_date",
            "sale_year",
            "sale_month",
            "sale_quarter",
            "sale_year_month",
            "address",
            "county",
            "eircode",
            "price_eur",
            "not_full_market_price",
            "is_not_full_market_price",
            "vat_exclusive",
            "is_vat_exclusive",
            "property_description",
            "is_new_property",
            "is_second_hand_property",
            "property_size_description",
            "property_size_category",
        ]
    ]

    print(
        "\nCleaning and transformation completed."
    )

    print(
        f"Rows removed: {removed_count:,}"
    )

    print(
        f"Rows remaining: {len(cleaned_df):,}"
    )

    print("\nTransformed columns:")

    for column in cleaned_df.columns:
        print(f"- {column}")

    print("\nData types:")

    print(
        cleaned_df.dtypes.to_string()
    )

    return cleaned_df


# ============================================================
# Main execution
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Load raw PPR data
    # --------------------------------------------------------

    df = load_ppr_data()

    # --------------------------------------------------------
    # Validate raw structure
    # --------------------------------------------------------

    validate_ppr_structure(df)

    # --------------------------------------------------------
    # Inspect raw data quality
    # --------------------------------------------------------

    validate_missing_values(df)

    validate_duplicates(df)

    inspect_duplicates(df)

    validate_duplicate_records(df)

    validate_sale_dates(df)

    validate_prices(df)

    inspect_counties(df)

    # --------------------------------------------------------
    # Clean and transform data
    # --------------------------------------------------------

    df = clean_ppr_data(df)

    # --------------------------------------------------------
    # Inspect cleaned data
    # --------------------------------------------------------

    inspect_price_range(df)

    inspect_highest_prices(df)

    inspect_property_classification(df)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print(
        "\nPPR data loaded and cleaned successfully."
    )

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print("\nColumns:")

    for column in df.columns:
        print(f"- {column}")

    print("\nSample cleaned prices:")

    print(
        df["price_eur"]
        .head(10)
        .to_string(index=False)
    )

    print(
        f"\nMinimum price: "
        f"€{df['price_eur'].min():,.2f}"
    )

    print(
        f"Maximum price: "
        f"€{df['price_eur'].max():,.2f}"
    )

    # --------------------------------------------------------
    # Save cleaned and transformed dataset
    # --------------------------------------------------------

    PROCESSED_DATA_DIR = (
        PROJECT_ROOT
        / "data"
        / "processed"
    )

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE = (
        PROCESSED_DATA_DIR
        / "ppr_cleaned.csv"
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\nCleaned PPR dataset saved to:"
    )

    print(OUTPUT_FILE)

    print(
        f"Saved rows: {len(df):,}"
    )

    print(
        f"Saved columns: {len(df.columns)}"
    )