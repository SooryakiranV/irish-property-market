from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
PPR_FILE = PROCESSED_DATA_DIR / "ppr_cleaned.csv"

EDA_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "ppr_eda"
EDA_TABLE_DIR = EDA_OUTPUT_DIR / "tables"
EDA_CHART_DIR = EDA_OUTPUT_DIR / "charts"

EDA_TABLE_DIR.mkdir(parents=True, exist_ok=True)
EDA_CHART_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Expected columns after transformation
# ============================================================

EXPECTED_COLUMNS = [
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


# ============================================================
# Utility functions
# ============================================================

def euro(value):
    """Format a numeric value as EUR."""
    if pd.isna(value):
        return "N/A"
    return f"€{value:,.0f}"


def save_table(df: pd.DataFrame, filename: str) -> None:
    """Save an analytical dataframe as CSV."""
    output_path = EDA_TABLE_DIR / filename
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved table: {output_path}")


def save_chart(filename: str) -> None:
    """Save the current matplotlib figure."""
    output_path = EDA_CHART_DIR / filename
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved chart: {output_path}")


# ============================================================
# Load and transform PPR data
# ============================================================

def load_ppr_data() -> pd.DataFrame:
    """
    Load the cleaned PPR dataset and apply the analytical
    transformations used by the project.
    """

    if not PPR_FILE.exists():
        raise FileNotFoundError(
            f"PPR file not found: {PPR_FILE}"
        )

    df = pd.read_csv(
        PPR_FILE,
        encoding="utf-8",
        low_memory=False,
    )

    # Remove exact duplicate records.
    df = df.drop_duplicates().copy()

    # --------------------------------------------------------
    # Rename columns if original PPR names are present
    # --------------------------------------------------------

    rename_map = {
        "Date of Sale (dd/mm/yyyy)": "sale_date",
        "Address": "address",
        "County": "county",
        "Eircode": "eircode",
        "Price (€)": "price_eur",
        "Price (â‚¬)": "price_eur",
        "Not Full Market Price": "not_full_market_price",
        "VAT Exclusive": "vat_exclusive",
        "Description of Property": "property_description",
        "Property Size Description": "property_size_description",
    }

    df = df.rename(
        columns={
            old: new
            for old, new in rename_map.items()
            if old in df.columns
        }
    )

    # --------------------------------------------------------
    # Validate core columns before analysis
    # --------------------------------------------------------

    required_core_columns = [
        "sale_date",
        "address",
        "county",
        "price_eur",
        "property_description",
    ]

    missing_core = [
        column
        for column in required_core_columns
        if column not in df.columns
    ]

    if missing_core:
        raise ValueError(
            f"Missing required PPR columns: {missing_core}"
        )

    # --------------------------------------------------------
    # Date transformation
    # --------------------------------------------------------

    df["sale_date"] = pd.to_datetime(
        df["sale_date"],
        errors="coerce",
    )

    if df["sale_date"].isna().any():
        invalid_dates = int(df["sale_date"].isna().sum())
        raise ValueError(
            f"PPR dataset contains {invalid_dates:,} invalid sale dates."
        )

    df["sale_year"] = (
        df["sale_date"].dt.year.astype("Int32")
    )

    df["sale_month"] = (
        df["sale_date"].dt.month.astype("Int32")
    )

    df["sale_quarter"] = (
        df["sale_date"].dt.quarter.astype("Int32")
    )

    df["sale_year_month"] = (
        df["sale_date"]
        .dt.to_period("M")
        .astype("string")
    )

    # --------------------------------------------------------
    # Text cleaning
    # --------------------------------------------------------

    text_columns = [
        "address",
        "county",
        "eircode",
        "not_full_market_price",
        "vat_exclusive",
        "property_description",
        "property_size_description",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # --------------------------------------------------------
    # Price transformation
    # --------------------------------------------------------

    df["price_eur"] = (
        df["price_eur"]
        .astype("string")
        .str.replace("€", "", regex=False)
        .str.replace("â‚¬", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df["price_eur"] = pd.to_numeric(
        df["price_eur"],
        errors="coerce",
    )

    if df["price_eur"].isna().any():
        invalid_prices = int(df["price_eur"].isna().sum())
        raise ValueError(
            f"PPR dataset contains {invalid_prices:,} invalid prices."
        )

    if (df["price_eur"] <= 0).any():
        invalid_prices = int(
            (df["price_eur"] <= 0).sum()
        )
        raise ValueError(
            f"PPR dataset contains {invalid_prices:,} "
            "non-positive prices."
        )

    # --------------------------------------------------------
    # Boolean flags
    # --------------------------------------------------------

    if "not_full_market_price" not in df.columns:
        df["not_full_market_price"] = pd.NA

    if "vat_exclusive" not in df.columns:
        df["vat_exclusive"] = pd.NA

    df["is_not_full_market_price"] = (
        df["not_full_market_price"]
        .astype("string")
        .str.lower()
        .eq("yes")
        .astype("boolean")
    )

    df["is_vat_exclusive"] = (
        df["vat_exclusive"]
        .astype("string")
        .str.lower()
        .eq("yes")
        .astype("boolean")
    )

    # --------------------------------------------------------
    # Property type flags
    # --------------------------------------------------------

    df["is_new_property"] = (
        df["property_description"]
        .astype("string")
        .str.lower()
        .str.contains(
            "new dwelling",
            na=False,
        )
        .astype("boolean")
    )

    df["is_second_hand_property"] = (
        df["property_description"]
        .astype("string")
        .str.lower()
        .str.contains(
            "second-hand dwelling",
            na=False,
        )
        .astype("boolean")
    )

    # --------------------------------------------------------
    # Property size categories
    # --------------------------------------------------------

    if "property_size_description" not in df.columns:
        df["property_size_description"] = pd.NA

    def classify_property_size(value):
        if pd.isna(value):
            return "Unknown"

        value = str(value).lower().strip()

        if "less than 38" in value:
            return "Less than 38 sq m"

        if (
            "greater than orequal to 38" in value
            or "greater than or equal to 38" in value
        ):
            if "less than 125" in value:
                return "38–124 sq m"

            if "greater than 125" in value:
                return "125+ sq m"

        if "greater than 125" in value:
            return "125+ sq m"

        return "Other / Unclassified"

    df["property_size_category"] = (
        df["property_size_description"]
        .apply(classify_property_size)
        .astype("string")
    )

    return df


# ============================================================
# Validate transformed structure
# ============================================================

def validate_structure(df: pd.DataFrame) -> None:
    """
    Verify that the transformed dataframe contains
    all expected analytical columns.
    """

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing transformed columns: {missing_columns}"
        )

    print("Analysis dataset structure validation passed.")


# ============================================================
# Basic dataset summary
# ============================================================

def dataset_summary(df: pd.DataFrame) -> None:
    """
    Display and save the basic PPR dataset summary.
    """

    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)

    summary = pd.DataFrame(
        {
            "metric": [
                "rows",
                "columns",
                "start_date",
                "end_date",
                "total_transaction_value",
                "mean_transaction_price",
                "median_transaction_price",
            ],
            "value": [
                len(df),
                len(df.columns),
                df["sale_date"].min().date(),
                df["sale_date"].max().date(),
                df["price_eur"].sum(),
                df["price_eur"].mean(),
                df["price_eur"].median(),
            ],
        }
    )

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(
        f"Date range: "
        f"{df['sale_date'].min().date()} "
        f"to "
        f"{df['sale_date'].max().date()}"
    )
    print(
        f"Total transaction value: "
        f"{euro(df['price_eur'].sum())}"
    )
    print(
        f"Mean transaction price: "
        f"{euro(df['price_eur'].mean())}"
    )
    print(
        f"Median transaction price: "
        f"{euro(df['price_eur'].median())}"
    )

    save_table(summary, "dataset_summary.csv")


# ============================================================
# Missing value analysis
# ============================================================

def analyse_missing_values(df: pd.DataFrame) -> None:
    """
    Analyse missing values in the transformed dataset.
    """

    print("\n" + "=" * 60)
    print("MISSING VALUE ANALYSIS")
    print("=" * 60)

    missing = (
        df.isna()
        .sum()
        .sort_values(ascending=False)
    )

    missing_percentage = (
        missing / len(df) * 100
    )

    missing_summary = pd.DataFrame(
        {
            "missing_count": missing,
            "missing_percentage": missing_percentage,
        }
    )

    print(
        missing_summary.to_string(
            float_format=lambda x: f"{x:.2f}"
        )
    )

    save_table(
        missing_summary.reset_index()
        .rename(columns={"index": "column"}),
        "missing_values.csv",
    )


# ============================================================
# Annual market analysis
# ============================================================

def analyse_yearly_transactions(df: pd.DataFrame) -> None:
    """
    Analyse annual transaction volume and prices.

    Growth metrics are calculated year-over-year.
    """

    print("\n" + "=" * 60)
    print("ANNUAL MARKET ANALYSIS")
    print("=" * 60)

    yearly = (
        df.groupby("sale_year")
        .agg(
            transactions=("price_eur", "size"),
            total_value=("price_eur", "sum"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
        .sort_values("sale_year")
    )

    yearly["transaction_growth_pct"] = (
        yearly["transactions"]
        .pct_change()
        * 100
    )

    yearly["median_price_growth_pct"] = (
        yearly["median_price"]
        .pct_change()
        * 100
    )

    yearly["mean_price_growth_pct"] = (
        yearly["mean_price"]
        .pct_change()
        * 100
    )

    print(
        yearly.to_string(
            index=False,
            formatters={
                "total_value": euro,
                "mean_price": euro,
                "median_price": euro,
                "transaction_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "median_price_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "mean_price_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
            },
        )
    )

    save_table(yearly, "annual_market_analysis.csv")

    # --------------------------------------------------------
    # Annual transaction volume chart
    # --------------------------------------------------------

    plt.figure(figsize=(11, 6))
    plt.plot(
        yearly["sale_year"],
        yearly["transactions"],
        marker="o",
    )
    plt.title("Annual Residential Property Transactions")
    plt.xlabel("Year")
    plt.ylabel("Number of Transactions")
    plt.grid(alpha=0.25)
    save_chart("annual_transaction_volume.png")

    # --------------------------------------------------------
    # Annual median price chart
    # --------------------------------------------------------

    plt.figure(figsize=(11, 6))
    plt.plot(
        yearly["sale_year"],
        yearly["median_price"],
        marker="o",
    )
    plt.title("Annual Median Residential Property Price")
    plt.xlabel("Year")
    plt.ylabel("Median Sale Price (€)")
    plt.grid(alpha=0.25)
    save_chart("annual_median_price.png")


# ============================================================
# Monthly market analysis
# ============================================================

def analyse_monthly_transactions(df: pd.DataFrame) -> None:
    """
    Analyse monthly transaction volume and median price.
    """

    print("\n" + "=" * 60)
    print("MONTHLY MARKET ANALYSIS")
    print("=" * 60)

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

    monthly["date"] = pd.to_datetime(
        monthly["sale_year_month"]
        .astype(str)
    )

    monthly = monthly.sort_values("date")

    monthly["transaction_growth_pct"] = (
        monthly["transactions"]
        .pct_change()
        * 100
    )

    monthly["median_price_growth_pct"] = (
        monthly["median_price"]
        .pct_change()
        * 100
    )

    print(
        monthly.tail(24).to_string(
            index=False,
            formatters={
                "total_value": euro,
                "mean_price": euro,
                "median_price": euro,
                "transaction_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "median_price_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
            },
        )
    )

    save_table(
        monthly.drop(columns=["date"]),
        "monthly_market_analysis.csv",
    )

    plt.figure(figsize=(12, 6))
    plt.plot(
        monthly["date"],
        monthly["transactions"],
    )
    plt.title("Monthly Residential Property Transactions")
    plt.xlabel("Date")
    plt.ylabel("Number of Transactions")
    plt.grid(alpha=0.25)
    save_chart("monthly_transaction_volume.png")

    plt.figure(figsize=(12, 6))
    plt.plot(
        monthly["date"],
        monthly["median_price"],
    )
    plt.title("Monthly Median Residential Property Price")
    plt.xlabel("Date")
    plt.ylabel("Median Sale Price (€)")
    plt.grid(alpha=0.25)
    save_chart("monthly_median_price.png")


# ============================================================
# Quarterly analysis
# ============================================================

def analyse_quarterly_transactions(df: pd.DataFrame) -> None:
    """
    Analyse quarterly transaction activity and prices.
    """

    print("\n" + "=" * 60)
    print("QUARTERLY MARKET ANALYSIS")
    print("=" * 60)

    quarterly = (
        df.groupby(
            ["sale_year", "sale_quarter"]
        )
        .agg(
            transactions=("price_eur", "size"),
            total_value=("price_eur", "sum"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
        .sort_values(
            ["sale_year", "sale_quarter"]
        )
    )

    quarterly["quarter_label"] = (
        quarterly["sale_year"].astype(str)
        + "-Q"
        + quarterly["sale_quarter"].astype(str)
    )

    quarterly["transaction_growth_pct"] = (
        quarterly["transactions"]
        .pct_change()
        * 100
    )

    quarterly["median_price_growth_pct"] = (
        quarterly["median_price"]
        .pct_change()
        * 100
    )

    print(
        quarterly.tail(20).to_string(
            index=False,
            formatters={
                "total_value": euro,
                "mean_price": euro,
                "median_price": euro,
                "transaction_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "median_price_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
            },
        )
    )

    save_table(
        quarterly,
        "quarterly_market_analysis.csv",
    )

    plt.figure(figsize=(12, 6))
    plt.plot(
        range(len(quarterly)),
        quarterly["transactions"],
    )
    plt.title("Quarterly Residential Property Transactions")
    plt.xlabel("Quarter")
    plt.ylabel("Number of Transactions")
    plt.grid(alpha=0.25)
    save_chart("quarterly_transaction_volume.png")


# ============================================================
# Seasonality analysis
# ============================================================

def analyse_seasonality(df: pd.DataFrame) -> None:
    """
    Analyse transaction activity by calendar month.

    This is descriptive seasonality analysis and does not
    imply causation.
    """

    print("\n" + "=" * 60)
    print("SEASONALITY ANALYSIS")
    print("=" * 60)

    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    seasonality = (
        df.groupby("sale_month")
        .agg(
            transactions=("price_eur", "size"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
    )

    seasonality["month_name"] = (
        seasonality["sale_month"]
        .map(month_names)
    )

    seasonality["average_transactions_per_year"] = (
        seasonality["transactions"]
        / df["sale_year"].nunique()
    )

    seasonality = seasonality.sort_values(
        "sale_month"
    )

    print(
        seasonality.to_string(
            index=False,
            formatters={
                "mean_price": euro,
                "median_price": euro,
                "average_transactions_per_year":
                    lambda x: f"{x:,.1f}",
            },
        )
    )

    save_table(
        seasonality,
        "monthly_seasonality.csv",
    )

    plt.figure(figsize=(11, 6))
    plt.bar(
        seasonality["month_name"],
        seasonality["transactions"],
    )
    plt.title("Residential Property Transactions by Calendar Month")
    plt.xlabel("Month")
    plt.ylabel("Total Transactions")
    plt.xticks(rotation=45)
    save_chart("transaction_seasonality.png")


# ============================================================
# County analysis
# ============================================================

def analyse_counties(df: pd.DataFrame) -> None:
    """
    Analyse county-level market activity, prices and
    national transaction share.
    """

    print("\n" + "=" * 60)
    print("COUNTY ANALYSIS")
    print("=" * 60)

    county_analysis = (
        df.groupby("county")
        .agg(
            transactions=("price_eur", "size"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
            total_value=("price_eur", "sum"),
        )
        .reset_index()
        .sort_values(
            "transactions",
            ascending=False,
        )
    )

    total_transactions = len(df)

    county_analysis["national_transaction_share_pct"] = (
        county_analysis["transactions"]
        / total_transactions
        * 100
    )

    print(
        county_analysis.to_string(
            index=False,
            formatters={
                "mean_price": euro,
                "median_price": euro,
                "total_value": euro,
                "national_transaction_share_pct":
                    lambda x: f"{x:.2f}%",
            },
        )
    )

    save_table(
        county_analysis,
        "county_market_analysis.csv",
    )

    # --------------------------------------------------------
    # County transaction volume chart
    # --------------------------------------------------------

    county_chart = county_analysis.sort_values(
        "transactions",
        ascending=True,
    )

    plt.figure(figsize=(10, 9))
    plt.barh(
        county_chart["county"],
        county_chart["transactions"],
    )
    plt.title("Residential Property Transactions by County")
    plt.xlabel("Number of Transactions")
    plt.ylabel("County")
    save_chart("county_transaction_volume.png")

    # --------------------------------------------------------
    # County median price chart
    # --------------------------------------------------------

    county_price_chart = county_analysis.sort_values(
        "median_price",
        ascending=True,
    )

    plt.figure(figsize=(10, 9))
    plt.barh(
        county_price_chart["county"],
        county_price_chart["median_price"],
    )
    plt.title("Median Residential Property Price by County")
    plt.xlabel("Median Sale Price (€)")
    plt.ylabel("County")
    save_chart("county_median_price.png")


# ============================================================
# County price growth analysis
# ============================================================

def analyse_county_price_growth(df: pd.DataFrame) -> None:
    """
    Calculate county-level median-price changes between
    the first and latest observed year for each county.

    Counties with insufficient observations are retained
    but marked as unavailable.
    """

    print("\n" + "=" * 60)
    print("COUNTY PRICE GROWTH ANALYSIS")
    print("=" * 60)

    county_year = (
        df.groupby(
            ["county", "sale_year"]
        )
        .agg(
            transactions=("price_eur", "size"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
        .sort_values(
            ["county", "sale_year"]
        )
    )

    rows = []

    for county, group in county_year.groupby("county"):
        group = group.sort_values("sale_year")

        first = group.iloc[0]
        latest = group.iloc[-1]

        first_year = int(first["sale_year"])
        latest_year = int(latest["sale_year"])

        first_price = float(first["median_price"])
        latest_price = float(latest["median_price"])

        if first_price > 0:
            growth = (
                (latest_price - first_price)
                / first_price
                * 100
            )
        else:
            growth = None

        rows.append(
            {
                "county": county,
                "first_year": first_year,
                "first_year_median_price": first_price,
                "latest_year": latest_year,
                "latest_year_median_price": latest_price,
                "median_price_growth_pct": growth,
                "first_year_transactions": int(
                    first["transactions"]
                ),
                "latest_year_transactions": int(
                    latest["transactions"]
                ),
            }
        )

    county_growth = pd.DataFrame(rows)

    print(
        county_growth.to_string(
            index=False,
            formatters={
                "first_year_median_price": euro,
                "latest_year_median_price": euro,
                "median_price_growth_pct":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
            },
        )
    )

    save_table(
        county_growth,
        "county_price_growth.csv",
    )


# ============================================================
# New vs second-hand analysis
# ============================================================

def analyse_new_vs_second_hand(df: pd.DataFrame) -> None:
    """
    Compare new and second-hand dwelling transactions using
    the analytical boolean flags already created.
    """

    print("\n" + "=" * 60)
    print("NEW VS SECOND-HAND ANALYSIS")
    print("=" * 60)

    conditions = [
        ("New", df["is_new_property"]),
        ("Second-Hand", df["is_second_hand_property"]),
    ]

    rows = []

    for label, mask in conditions:
        subset = df.loc[mask.fillna(False)]

        rows.append(
            {
                "property_type": label,
                "transactions": len(subset),
                "transaction_share_pct": (
                    len(subset) / len(df) * 100
                ),
                "mean_price": (
                    subset["price_eur"].mean()
                    if len(subset)
                    else None
                ),
                "median_price": (
                    subset["price_eur"].median()
                    if len(subset)
                    else None
                ),
                "total_value": (
                    subset["price_eur"].sum()
                    if len(subset)
                    else 0
                ),
            }
        )

    comparison = pd.DataFrame(rows)

    print(
        comparison.to_string(
            index=False,
            formatters={
                "transaction_share_pct":
                    lambda x: f"{x:.2f}%",
                "mean_price": euro,
                "median_price": euro,
                "total_value": euro,
            },
        )
    )

    save_table(
        comparison,
        "new_vs_second_hand.csv",
    )

    plt.figure(figsize=(8, 6))
    plt.bar(
        comparison["property_type"],
        comparison["transactions"],
    )
    plt.title("New vs Second-Hand Transactions")
    plt.xlabel("Property Type")
    plt.ylabel("Transactions")
    save_chart("new_vs_second_hand_transactions.png")

    plt.figure(figsize=(8, 6))
    plt.bar(
        comparison["property_type"],
        comparison["median_price"],
    )
    plt.title("Median Price: New vs Second-Hand")
    plt.xlabel("Property Type")
    plt.ylabel("Median Sale Price (€)")
    save_chart("new_vs_second_hand_median_price.png")


# ============================================================
# Property description analysis
# ============================================================

def analyse_property_descriptions(df: pd.DataFrame) -> None:
    """
    Analyse the original property description categories.
    """

    print("\n" + "=" * 60)
    print("PROPERTY DESCRIPTION ANALYSIS")
    print("=" * 60)

    description_analysis = (
        df.groupby("property_description")
        .agg(
            transactions=("price_eur", "size"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
        .sort_values(
            "transactions",
            ascending=False,
        )
    )

    print(
        description_analysis.to_string(
            index=False,
            formatters={
                "mean_price": euro,
                "median_price": euro,
            },
        )
    )

    save_table(
        description_analysis,
        "property_description_analysis.csv",
    )


# ============================================================
# Property size analysis
# ============================================================

def analyse_property_size(df: pd.DataFrame) -> None:
    """
    Analyse transactions by property size category.
    """

    print("\n" + "=" * 60)
    print("PROPERTY SIZE ANALYSIS")
    print("=" * 60)

    size_analysis = (
        df.groupby("property_size_category")
        .agg(
            transactions=("price_eur", "size"),
            mean_price=("price_eur", "mean"),
            median_price=("price_eur", "median"),
        )
        .reset_index()
        .sort_values(
            "transactions",
            ascending=False,
        )
    )

    size_analysis["transaction_share_pct"] = (
        size_analysis["transactions"]
        / len(df)
        * 100
    )

    print(
        size_analysis.to_string(
            index=False,
            formatters={
                "mean_price": euro,
                "median_price": euro,
                "transaction_share_pct":
                    lambda x: f"{x:.2f}%",
            },
        )
    )

    save_table(
        size_analysis,
        "property_size_analysis.csv",
    )

    plt.figure(figsize=(10, 6))
    plt.bar(
        size_analysis["property_size_category"],
        size_analysis["transactions"],
    )
    plt.title("Transactions by Property Size Category")
    plt.xlabel("Property Size Category")
    plt.ylabel("Transactions")
    plt.xticks(rotation=30)
    save_chart("property_size_distribution.png")


# ============================================================
# Non-full-market-price analysis
# ============================================================

def analyse_non_full_market_price(df: pd.DataFrame) -> None:
    """
    Analyse transactions marked as not being full market price.
    """

    print("\n" + "=" * 60)
    print("NON-FULL-MARKET-PRICE ANALYSIS")
    print("=" * 60)

    rows = []

    for label, mask in [
        (
            "Full Market Price",
            ~df["is_not_full_market_price"].fillna(False),
        ),
        (
            "Not Full Market Price",
            df["is_not_full_market_price"].fillna(False),
        ),
    ]:
        subset = df.loc[mask]

        rows.append(
            {
                "market_price_category": label,
                "transactions": len(subset),
                "transaction_share_pct": (
                    len(subset) / len(df) * 100
                ),
                "mean_price": subset["price_eur"].mean(),
                "median_price": subset["price_eur"].median(),
            }
        )

    analysis = pd.DataFrame(rows)

    print(
        analysis.to_string(
            index=False,
            formatters={
                "transaction_share_pct":
                    lambda x: f"{x:.2f}%",
                "mean_price": euro,
                "median_price": euro,
            },
        )
    )

    save_table(
        analysis,
        "non_full_market_price_analysis.csv",
    )


# ============================================================
# VAT-exclusive analysis
# ============================================================

def analyse_vat_exclusive(df: pd.DataFrame) -> None:
    """
    Analyse transactions marked as VAT-exclusive.
    """

    print("\n" + "=" * 60)
    print("VAT-EXCLUSIVE ANALYSIS")
    print("=" * 60)

    rows = []

    for label, mask in [
        (
            "Not VAT Exclusive",
            ~df["is_vat_exclusive"].fillna(False),
        ),
        (
            "VAT Exclusive",
            df["is_vat_exclusive"].fillna(False),
        ),
    ]:
        subset = df.loc[mask]

        rows.append(
            {
                "vat_category": label,
                "transactions": len(subset),
                "transaction_share_pct": (
                    len(subset) / len(df) * 100
                ),
                "mean_price": subset["price_eur"].mean(),
                "median_price": subset["price_eur"].median(),
            }
        )

    analysis = pd.DataFrame(rows)

    print(
        analysis.to_string(
            index=False,
            formatters={
                "transaction_share_pct":
                    lambda x: f"{x:.2f}%",
                "mean_price": euro,
                "median_price": euro,
            },
        )
    )

    save_table(
        analysis,
        "vat_exclusive_analysis.csv",
    )


# ============================================================
# Price distribution analysis
# ============================================================

def analyse_price_distribution(df: pd.DataFrame) -> None:
    """
    Analyse price distribution using robust descriptive
    statistics and percentiles.
    """

    print("\n" + "=" * 60)
    print("PRICE DISTRIBUTION")
    print("=" * 60)

    percentiles = df["price_eur"].quantile(
        [
            0.01,
            0.05,
            0.10,
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99,
            0.995,
            0.999,
        ]
    )

    print(f"Minimum: {euro(df['price_eur'].min())}")

    for percentile, value in percentiles.items():
        print(
            f"{percentile * 100:.1f}th percentile: "
            f"{euro(value)}"
        )

    print(f"Maximum: {euro(df['price_eur'].max())}")

    distribution = pd.DataFrame(
        {
            "percentile": [
                f"{p * 100:.1f}%"
                for p in percentiles.index
            ],
            "price_eur": percentiles.values,
        }
    )

    save_table(
        distribution,
        "price_percentiles.csv",
    )

    # Histogram using a capped view so that extreme
    # development transactions do not compress the
    # ordinary residential distribution.
    p99 = df["price_eur"].quantile(0.99)

    regular_prices = df.loc[
        df["price_eur"] <= p99,
        "price_eur",
    ]

    plt.figure(figsize=(11, 6))
    plt.hist(
        regular_prices,
        bins=50,
    )
    plt.title(
        "Residential Property Price Distribution "
        "(up to 99th percentile)"
    )
    plt.xlabel("Sale Price (€)")
    plt.ylabel("Transactions")
    save_chart("price_distribution_up_to_99th_percentile.png")


# ============================================================
# Extreme transaction investigation
# ============================================================

def analyse_high_value_transactions(
    df: pd.DataFrame,
) -> None:
    """
    Investigate unusually large transactions.

    Extreme records are NOT deleted. They are flagged and
    retained because some represent legitimate multi-unit
    developments or large property transactions.
    """

    print("\n" + "=" * 60)
    print("EXTREME TRANSACTION ANALYSIS")
    print("=" * 60)

    p99 = df["price_eur"].quantile(0.99)
    p995 = df["price_eur"].quantile(0.995)
    p999 = df["price_eur"].quantile(0.999)

    print(f"99th percentile:  {euro(p99)}")
    print(f"99.5th percentile: {euro(p995)}")
    print(f"99.9th percentile: {euro(p999)}")

    extreme = df.loc[
        df["price_eur"] >= p999
    ].copy()

    extreme["price_percentile_group"] = ">= 99.9th percentile"

    columns = [
        "sale_date",
        "address",
        "county",
        "price_eur",
        "property_description",
        "is_new_property",
        "is_second_hand_property",
        "is_not_full_market_price",
        "is_vat_exclusive",
    ]

    extreme = extreme[
        [
            column
            for column in columns
            if column in extreme.columns
        ]
    ].sort_values(
        "price_eur",
        ascending=False,
    )

    print("\nTransactions at or above the 99.9th percentile:")
    print(
        extreme.head(50).to_string(
            index=False,
            formatters={
                "price_eur": euro,
            },
        )
    )

    save_table(
        extreme,
        "extreme_transactions_99_9th_percentile.csv",
    )

    # --------------------------------------------------------
    # Compare ordinary and extreme transaction views
    # --------------------------------------------------------

    standard = df.loc[
        df["price_eur"] < p999
    ]

    comparison = pd.DataFrame(
        {
            "analytical_view": [
                "All transactions",
                "Below 99.9th percentile",
                "At or above 99.9th percentile",
            ],
            "transactions": [
                len(df),
                len(standard),
                len(extreme),
            ],
            "mean_price": [
                df["price_eur"].mean(),
                standard["price_eur"].mean(),
                extreme["price_eur"].mean(),
            ],
            "median_price": [
                df["price_eur"].median(),
                standard["price_eur"].median(),
                extreme["price_eur"].median(),
            ],
        }
    )

    print("\nAnalytical view comparison:")
    print(
        comparison.to_string(
            index=False,
            formatters={
                "mean_price": euro,
                "median_price": euro,
            },
        )
    )

    save_table(
        comparison,
        "extreme_transaction_comparison.csv",
    )


# ============================================================
# Data quality summary for EDA
# ============================================================

def analyse_eda_quality(df: pd.DataFrame) -> None:
    """
    Produce a compact quality summary used to document
    important analytical limitations.
    """

    print("\n" + "=" * 60)
    print("EDA DATA QUALITY SUMMARY")
    print("=" * 60)

    quality = pd.DataFrame(
        {
            "metric": [
                "row_count",
                "invalid_dates",
                "invalid_prices",
                "missing_eircode",
                "missing_property_size_description",
                "not_full_market_price_transactions",
                "vat_exclusive_transactions",
                "new_property_transactions",
                "second_hand_property_transactions",
            ],
            "value": [
                len(df),
                int(df["sale_date"].isna().sum()),
                int(df["price_eur"].isna().sum()),
                int(df["eircode"].isna().sum()),
                int(
                    df[
                        "property_size_description"
                    ].isna().sum()
                ),
                int(
                    df[
                        "is_not_full_market_price"
                    ].fillna(False).sum()
                ),
                int(
                    df[
                        "is_vat_exclusive"
                    ].fillna(False).sum()
                ),
                int(
                    df[
                        "is_new_property"
                    ].fillna(False).sum()
                ),
                int(
                    df[
                        "is_second_hand_property"
                    ].fillna(False).sum()
                ),
            ],
        }
    )

    print(
        quality.to_string(index=False)
    )

    save_table(
        quality,
        "eda_quality_summary.csv",
    )


# ============================================================
# Main execution
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PPR EXPLORATORY DATA ANALYSIS")
    print("=" * 60)

    print("\nLoading PPR analysis dataset...")

    df = load_ppr_data()

    print(
        f"Loaded {len(df):,} PPR transactions."
    )

    validate_structure(df)

    # --------------------------------------------------------
    # Core dataset inspection
    # --------------------------------------------------------

    dataset_summary(df)
    analyse_missing_values(df)
    analyse_eda_quality(df)

    # --------------------------------------------------------
    # National market
    # --------------------------------------------------------

    analyse_yearly_transactions(df)
    analyse_monthly_transactions(df)
    analyse_quarterly_transactions(df)
    analyse_seasonality(df)

    # --------------------------------------------------------
    # Geography
    # --------------------------------------------------------

    analyse_counties(df)
    analyse_county_price_growth(df)

    # --------------------------------------------------------
    # Property characteristics
    # --------------------------------------------------------

    analyse_new_vs_second_hand(df)
    analyse_property_descriptions(df)
    analyse_property_size(df)

    # --------------------------------------------------------
    # Transaction characteristics
    # --------------------------------------------------------

    analyse_non_full_market_price(df)
    analyse_vat_exclusive(df)

    # --------------------------------------------------------
    # Price distribution and extremes
    # --------------------------------------------------------

    analyse_price_distribution(df)
    analyse_high_value_transactions(df)

    # --------------------------------------------------------
    # Completion
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("PPR EDA COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(f"\nEDA outputs saved to:")
    print(EDA_OUTPUT_DIR)

    print("\nTables:")
    print(EDA_TABLE_DIR)

    print("\nCharts:")
    print(EDA_CHART_DIR)

    print("\nNext project stage:")
    print("STEP 2 — CSO DATA INVESTIGATION")