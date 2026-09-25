"""
Irish Property Market Analysis
===============================

Stage 3 of the Irish Property Market Analysis project.

Purpose
-------
Analyse the existing PostgreSQL analytics tables:

    analytics.monthly_market
    analytics.county_market
    analytics.planning_activity

The script produces:

    1. National market trends
    2. Year-on-year price growth
    3. County comparisons
    4. New vs second-hand property analysis
    5. Planning activity analysis
    6. Market vs planning activity correlation
    7. Project KPI summary

Important
---------
2026 is a partial year in the current dataset.

Therefore:
    - Full-year comparisons use completed years only.
    - 2026 is reported separately as YTD.
    - Jan-Sep comparisons are used where appropriate.
    - The latest available month is detected from the data rather than
      assuming September.

This script does not modify any database tables.
It only reads from PostgreSQL and writes CSV analysis outputs.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db_config import create_postgres_engine


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

CURRENT_PARTIAL_YEAR = 2026
LATEST_COMPLETED_YEAR = 2025
BASELINE_YEAR = 2010

# The current project treats 2026 as a partial year.
# This can be changed if the project is updated later.
PARTIAL_YEAR = CURRENT_PARTIAL_YEAR


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_engine():
    """
    Create and return the PostgreSQL SQLAlchemy engine.
    """
    return create_postgres_engine()


# ============================================================
# LOAD MONTHLY MARKET DATA
# ============================================================

def load_monthly_market(engine) -> pd.DataFrame:
    """
    Load national monthly property-market data.
    """

    query = text(
        """
        SELECT
            year_month,
            month_start,
            transactions,
            total_value,
            mean_price,
            median_price,
            national_rppi
        FROM analytics.monthly_market
        ORDER BY month_start
        """
    )

    df = pd.read_sql(query, engine)

    if df.empty:
        raise ValueError(
            "analytics.monthly_market returned no rows."
        )

    df["month_start"] = pd.to_datetime(
        df["month_start"],
        errors="coerce",
    )

    if df["month_start"].isna().any():
        raise ValueError(
            "monthly_market contains invalid month_start values."
        )

    numeric_columns = [
        "transactions",
        "total_value",
        "mean_price",
        "median_price",
        "national_rppi",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.sort_values("month_start").reset_index(drop=True)

    return df


# ============================================================
# LOAD COUNTY MARKET DATA
# ============================================================

def load_county_market(engine) -> pd.DataFrame:
    """
    Load county-level annual property-market data.
    """

    query = text(
        """
        SELECT
            county,
            sale_year,
            transactions,
            total_value,
            mean_price,
            median_price,
            new_property_transactions,
            second_hand_property_transactions
        FROM analytics.county_market
        ORDER BY sale_year, county
        """
    )

    df = pd.read_sql(query, engine)

    if df.empty:
        raise ValueError(
            "analytics.county_market returned no rows."
        )

    numeric_columns = [
        "sale_year",
        "transactions",
        "total_value",
        "mean_price",
        "median_price",
        "new_property_transactions",
        "second_hand_property_transactions",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=["county", "sale_year"]
    ).copy()

    df["sale_year"] = df["sale_year"].astype(int)

    return df


# ============================================================
# LOAD PLANNING ACTIVITY DATA
# ============================================================

def load_planning_activity(engine) -> pd.DataFrame:
    """
    Load monthly planning activity data.
    """

    query = text(
        """
        SELECT
            planning_authority,
            year_month,
            month_start,
            applications,
            granted_applications,
            refused_applications,
            residential_units
        FROM analytics.planning_activity
        ORDER BY month_start, planning_authority
        """
    )

    df = pd.read_sql(query, engine)

    if df.empty:
        raise ValueError(
            "analytics.planning_activity returned no rows."
        )

    df["month_start"] = pd.to_datetime(
        df["month_start"],
        errors="coerce",
    )

    if df["month_start"].isna().any():
        raise ValueError(
            "planning_activity contains invalid month_start values."
        )

    numeric_columns = [
        "applications",
        "granted_applications",
        "refused_applications",
        "residential_units",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.sort_values(
        ["month_start", "planning_authority"]
    ).reset_index(drop=True)

    return df


# ============================================================
# HELPER — DETERMINE AVAILABLE PERIOD
# ============================================================

def get_latest_month(df: pd.DataFrame) -> pd.Timestamp:
    """
    Return the latest month available in a dataframe.
    """

    if df.empty:
        raise ValueError(
            "Cannot determine latest month from an empty dataframe."
        )

    latest_month = df["month_start"].max()

    if pd.isna(latest_month):
        raise ValueError(
            "No valid month_start values were found."
        )

    return pd.Timestamp(latest_month)


# ============================================================
# ANALYSIS 1 — NATIONAL MARKET TREND
# ============================================================

def analyse_national_market(
    monthly_market: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Produce:

    1. Full-year national market summary for completed years.
    2. Partial-year YTD summary for the current partial year.

    Annual transaction counts and transaction values are summed.

    Average monthly mean price, median price and RPPI are calculated
    from the monthly observations.
    """

    df = monthly_market.copy()

    df["year"] = df["month_start"].dt.year

    # --------------------------------------------------------
    # Determine completed years from the data
    # --------------------------------------------------------

    full_year_df = df[
        df["year"] < PARTIAL_YEAR
    ].copy()

    annual = (
        full_year_df
        .groupby("year", as_index=False)
        .agg(
            transactions=("transactions", "sum"),
            total_value=("total_value", "sum"),
            avg_monthly_mean_price=("mean_price", "mean"),
            avg_monthly_median_price=("median_price", "mean"),
            avg_rppi=("national_rppi", "mean"),
        )
    )

    annual["total_value"] = annual[
        "total_value"
    ].round(2)

    annual["avg_monthly_mean_price"] = annual[
        "avg_monthly_mean_price"
    ].round(2)

    annual["avg_monthly_median_price"] = annual[
        "avg_monthly_median_price"
    ].round(2)

    annual["avg_rppi"] = annual[
        "avg_rppi"
    ].round(2)

    annual["period"] = "Full Year"

    annual_output = annual[
        [
            "year",
            "period",
            "transactions",
            "total_value",
            "avg_monthly_mean_price",
            "avg_monthly_median_price",
            "avg_rppi",
        ]
    ].copy()

    # --------------------------------------------------------
    # Partial year / YTD
    # --------------------------------------------------------

    ytd_df = df[
        df["year"] == PARTIAL_YEAR
    ].copy()

    if ytd_df.empty:

        ytd_output = pd.DataFrame(
            [
                {
                    "year": PARTIAL_YEAR,
                    "period": "No data",
                    "transactions": 0,
                    "total_value": 0.0,
                    "avg_monthly_mean_price": None,
                    "avg_monthly_median_price": None,
                    "avg_rppi": None,
                }
            ]
        )

    else:

        latest_month = get_latest_month(ytd_df)

        period = (
            f"January-{latest_month.strftime('%B')}"
        )

        ytd_output = pd.DataFrame(
            [
                {
                    "year": PARTIAL_YEAR,
                    "period": period,
                    "transactions": ytd_df[
                        "transactions"
                    ].sum(),
                    "total_value": ytd_df[
                        "total_value"
                    ].sum(),
                    "avg_monthly_mean_price": ytd_df[
                        "mean_price"
                    ].mean(),
                    "avg_monthly_median_price": ytd_df[
                        "median_price"
                    ].mean(),
                    "avg_rppi": ytd_df[
                        "national_rppi"
                    ].mean(),
                }
            ]
        )

        ytd_output["total_value"] = ytd_output[
            "total_value"
        ].round(2)

        ytd_output["avg_monthly_mean_price"] = (
            ytd_output[
                "avg_monthly_mean_price"
            ].round(2)
        )

        ytd_output["avg_monthly_median_price"] = (
            ytd_output[
                "avg_monthly_median_price"
            ].round(2)
        )

        ytd_output["avg_rppi"] = (
            ytd_output["avg_rppi"].round(2)
        )

    return annual_output, ytd_output


# ============================================================
# ANALYSIS 2 — YEAR-ON-YEAR PRICE GROWTH
# ============================================================

def analyse_price_growth(
    monthly_market: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate annual price growth using completed years.

    Growth is calculated from annual averages of the monthly values:

        mean price
        median price
        national RPPI

    Partial-year data is excluded.
    """

    df = monthly_market.copy()

    df["year"] = df["month_start"].dt.year

    df = df[
        df["year"] < PARTIAL_YEAR
    ].copy()

    annual = (
        df
        .groupby("year", as_index=False)
        .agg(
            avg_mean_price=("mean_price", "mean"),
            avg_median_price=("median_price", "mean"),
            avg_rppi=("national_rppi", "mean"),
        )
    )

    annual = annual.sort_values(
        "year"
    ).reset_index(drop=True)

    annual["mean_price_yoy_pct"] = (
        annual["avg_mean_price"]
        .pct_change(fill_method=None)
        * 100
    )

    annual["median_price_yoy_pct"] = (
        annual["avg_median_price"]
        .pct_change(fill_method=None)
        * 100
    )

    annual["rppi_yoy_pct"] = (
        annual["avg_rppi"]
        .pct_change(fill_method=None)
        * 100
    )

    growth_columns = [
        "avg_mean_price",
        "avg_median_price",
        "avg_rppi",
        "mean_price_yoy_pct",
        "median_price_yoy_pct",
        "rppi_yoy_pct",
    ]

    annual[growth_columns] = annual[
        growth_columns
    ].round(2)

    return annual


# ============================================================
# ANALYSIS 3 — COUNTY COMPARISON
# ============================================================

def analyse_counties(
    county_market: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Produce three county-level analyses:

    1. Latest completed year comparison.
    2. County price change from 2010 to the latest completed year.
    3. New vs second-hand transactions for the latest completed year.
    """

    df = county_market.copy()

    if df.empty:
        raise ValueError(
            "County market dataframe is empty."
        )

    # --------------------------------------------------------
    # Determine latest completed year
    # --------------------------------------------------------

    available_years = sorted(
        df["sale_year"].dropna().unique()
    )

    completed_years = [
        int(year)
        for year in available_years
        if int(year) < PARTIAL_YEAR
    ]

    if not completed_years:
        raise ValueError(
            "No completed county-market years available."
        )

    comparison_year = max(completed_years)

    # --------------------------------------------------------
    # Latest completed year
    # --------------------------------------------------------

    latest = df[
        df["sale_year"] == comparison_year
    ].copy()

    latest = latest.sort_values(
        "transactions",
        ascending=False,
    )

    numeric_columns = [
        "total_value",
        "mean_price",
        "median_price",
    ]

    for column in numeric_columns:
        latest[column] = latest[column].round(2)

    latest_output = latest[
        [
            "county",
            "sale_year",
            "transactions",
            "total_value",
            "mean_price",
            "median_price",
            "new_property_transactions",
            "second_hand_property_transactions",
        ]
    ].reset_index(drop=True)

    # --------------------------------------------------------
    # 2010 vs latest completed year
    # --------------------------------------------------------

    comparison = df[
        df["sale_year"].isin(
            [BASELINE_YEAR, comparison_year]
        )
    ].copy()

    price_pivot = comparison.pivot_table(
        index="county",
        columns="sale_year",
        values="mean_price",
        aggfunc="first",
    )

    if (
        BASELINE_YEAR in price_pivot.columns
        and comparison_year in price_pivot.columns
    ):

        price_change = (
            price_pivot
            .reset_index()
            .copy()
        )

        baseline_values = price_change[
            BASELINE_YEAR
        ]

        comparison_values = price_change[
            comparison_year
        ]

        price_change["price_change_pct"] = (
            (
                comparison_values
                - baseline_values
            )
            / baseline_values.replace(0, pd.NA)
        ) * 100

        price_change = price_change[
            [
                "county",
                BASELINE_YEAR,
                comparison_year,
                "price_change_pct",
            ]
        ]

        price_change = price_change.rename(
            columns={
                BASELINE_YEAR: (
                    f"mean_price_{BASELINE_YEAR}"
                ),
                comparison_year: (
                    f"mean_price_{comparison_year}"
                ),
            }
        )

        price_change[
            f"mean_price_{BASELINE_YEAR}"
        ] = price_change[
            f"mean_price_{BASELINE_YEAR}"
        ].round(2)

        price_change[
            f"mean_price_{comparison_year}"
        ] = price_change[
            f"mean_price_{comparison_year}"
        ].round(2)

        price_change[
            "price_change_pct"
        ] = price_change[
            "price_change_pct"
        ].round(2)

        price_change = price_change.sort_values(
            "price_change_pct",
            ascending=False,
        ).reset_index(drop=True)

    else:

        price_change = pd.DataFrame(
            columns=[
                "county",
                f"mean_price_{BASELINE_YEAR}",
                f"mean_price_{comparison_year}",
                "price_change_pct",
            ]
        )

    # --------------------------------------------------------
    # New vs second-hand property mix
    # --------------------------------------------------------

    property_mix = latest_output.copy()

    property_mix[
        "total_classified_transactions"
    ] = (
        property_mix[
            "new_property_transactions"
        ].fillna(0)
        + property_mix[
            "second_hand_property_transactions"
        ].fillna(0)
    )

    classified_total = property_mix[
        "total_classified_transactions"
    ]

    property_mix[
        "new_property_share_pct"
    ] = (
        property_mix[
            "new_property_transactions"
        ]
        / classified_total.replace(0, pd.NA)
        * 100
    )

    property_mix[
        "second_hand_property_share_pct"
    ] = (
        property_mix[
            "second_hand_property_transactions"
        ]
        / classified_total.replace(0, pd.NA)
        * 100
    )

    property_mix[
        "new_property_share_pct"
    ] = property_mix[
        "new_property_share_pct"
    ].round(2)

    property_mix[
        "second_hand_property_share_pct"
    ] = property_mix[
        "second_hand_property_share_pct"
    ].round(2)

    property_mix = property_mix[
        [
            "county",
            "sale_year",
            "new_property_transactions",
            "second_hand_property_transactions",
            "total_classified_transactions",
            "new_property_share_pct",
            "second_hand_property_share_pct",
        ]
    ]

    return (
        latest_output,
        price_change,
        property_mix,
    )


# ============================================================
# ANALYSIS 4 — PLANNING ACTIVITY
# ============================================================

def analyse_planning_activity(
    planning_activity: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Produce:

    1. Annual national planning activity.
    2. Planning activity by authority for the latest completed year.

    Partial-year data is excluded from full-year analysis.
    """

    df = planning_activity.copy()

    df["year"] = df["month_start"].dt.year

    # --------------------------------------------------------
    # Annual national planning activity
    # --------------------------------------------------------

    full_year_df = df[
        df["year"] < PARTIAL_YEAR
    ].copy()

    annual = (
        full_year_df
        .groupby("year", as_index=False)
        .agg(
            applications=("applications", "sum"),
            granted_applications=(
                "granted_applications",
                "sum",
            ),
            refused_applications=(
                "refused_applications",
                "sum",
            ),
            residential_units=(
                "residential_units",
                "sum",
            ),
        )
    )

    annual["grant_rate_pct"] = (
        annual["granted_applications"]
        / annual["applications"].replace(0, pd.NA)
        * 100
    )

    annual["refusal_rate_pct"] = (
        annual["refused_applications"]
        / annual["applications"].replace(0, pd.NA)
        * 100
    )

    annual[
        [
            "grant_rate_pct",
            "refusal_rate_pct",
        ]
    ] = annual[
        [
            "grant_rate_pct",
            "refusal_rate_pct",
        ]
    ].round(2)

    # --------------------------------------------------------
    # Latest completed year
    # --------------------------------------------------------

    available_years = sorted(
        df["year"].dropna().unique()
    )

    completed_years = [
        int(year)
        for year in available_years
        if int(year) < PARTIAL_YEAR
    ]

    if not completed_years:
        raise ValueError(
            "No completed planning years available."
        )

    comparison_year = max(completed_years)

    authority = (
        df[
            df["year"] == comparison_year
        ]
        .groupby(
            "planning_authority",
            as_index=False,
        )
        .agg(
            applications=("applications", "sum"),
            granted_applications=(
                "granted_applications",
                "sum",
            ),
            refused_applications=(
                "refused_applications",
                "sum",
            ),
            residential_units=(
                "residential_units",
                "sum",
            ),
        )
    )

    authority["grant_rate_pct"] = (
        authority["granted_applications"]
        / authority["applications"].replace(0, pd.NA)
        * 100
    )

    authority["refusal_rate_pct"] = (
        authority["refused_applications"]
        / authority["applications"].replace(0, pd.NA)
        * 100
    )

    authority[
        [
            "grant_rate_pct",
            "refusal_rate_pct",
        ]
    ] = authority[
        [
            "grant_rate_pct",
            "refusal_rate_pct",
        ]
    ].round(2)

    authority = authority.sort_values(
        "applications",
        ascending=False,
    ).reset_index(drop=True)

    return annual, authority


# ============================================================
# ANALYSIS 5 — MARKET VS PLANNING ACTIVITY
# ============================================================

def analyse_market_vs_planning(
    monthly_market: pd.DataFrame,
    planning_activity: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine monthly national property-market activity with
    national planning activity.

    Pearson correlations are calculated between:

        Property transactions
        Mean property price
        Median property price
        RPPI

    and:

        Planning applications
        Granted applications
        Refused applications
        Residential units

    The analysis measures statistical association only.

    It does NOT establish causation.

    The correlation uses the common overlapping monthly period
    between the two datasets.
    """

    # --------------------------------------------------------
    # Aggregate planning activity nationally by month
    # --------------------------------------------------------

    planning_monthly = (
        planning_activity
        .groupby(
            "month_start",
            as_index=False,
        )
        .agg(
            applications=(
                "applications",
                "sum",
            ),
            granted_applications=(
                "granted_applications",
                "sum",
            ),
            refused_applications=(
                "refused_applications",
                "sum",
            ),
            residential_units=(
                "residential_units",
                "sum",
            ),
        )
    )

    # --------------------------------------------------------
    # Prepare market data
    # --------------------------------------------------------

    market = monthly_market.copy()

    market["month_start"] = pd.to_datetime(
        market["month_start"]
    )

    market_columns = [
        "transactions",
        "mean_price",
        "median_price",
        "national_rppi",
    ]

    planning_columns = [
        "applications",
        "granted_applications",
        "refused_applications",
        "residential_units",
    ]

    # --------------------------------------------------------
    # Merge on month
    # --------------------------------------------------------

    merged = market[
        [
            "month_start"
        ] + market_columns
    ].merge(
        planning_monthly[
            [
                "month_start"
            ] + planning_columns
        ],
        on="month_start",
        how="inner",
    )

    if merged.empty:
        raise ValueError(
            "No overlapping months exist between "
            "market and planning datasets."
        )

    merged = merged.sort_values(
        "month_start"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Restrict to complete cases
    # --------------------------------------------------------

    correlation_columns = (
        market_columns
        + planning_columns
    )

    complete_data = merged[
        correlation_columns
    ].dropna().copy()

    if len(complete_data) < 3:
        raise ValueError(
            "Insufficient complete monthly observations "
            "for Pearson correlation analysis."
        )

    # --------------------------------------------------------
    # Calculate correlations using pairwise complete cases
    # --------------------------------------------------------

    results = []

    for market_column in market_columns:

        for planning_column in planning_columns:

            pair_data = merged[
                [
                    market_column,
                    planning_column,
                ]
            ].dropna()

            if len(pair_data) < 3:
                correlation = float("nan")
            else:
                correlation = pair_data[
                    market_column
                ].corr(
                    pair_data[
                        planning_column
                    ]
                )

            results.append(
                {
                    "market_metric": market_column,
                    "planning_metric": planning_column,
                    "pearson_correlation": correlation,
                    "observations": len(pair_data),
                }
            )

    correlation_df = pd.DataFrame(results)

    correlation_df[
        "pearson_correlation"
    ] = correlation_df[
        "pearson_correlation"
    ].round(4)

    # Add period metadata so the result is transparent.
    correlation_df["period_start"] = (
        merged["month_start"].min()
    )

    correlation_df["period_end"] = (
        merged["month_start"].max()
    )

    return correlation_df


# ============================================================
# ANALYSIS 6 — KEY PROJECT KPIs
# ============================================================

def calculate_key_kpis(
    monthly_market: pd.DataFrame,
    county_market: pd.DataFrame,
    planning_activity: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce a compact KPI table suitable for the final dashboard.

    KPIs are based on the latest completed year (normally 2025)
    plus 2026 YTD market activity.
    """

    market = monthly_market.copy()
    county = county_market.copy()
    planning = planning_activity.copy()

    market["year"] = (
        market["month_start"].dt.year
    )

    planning["year"] = (
        planning["month_start"].dt.year
    )

    # --------------------------------------------------------
    # Completed-year market data
    # --------------------------------------------------------

    market_completed = market[
        market["year"] < PARTIAL_YEAR
    ].copy()

    if market_completed.empty:
        raise ValueError(
            "No completed market data available for KPI calculation."
        )

    latest_completed_market_year = int(
        market_completed["year"].max()
    )

    market_latest = market_completed[
        market_completed["year"]
        == latest_completed_market_year
    ].copy()

    transactions_latest = int(
        market_latest[
            "transactions"
        ].sum()
    )

    total_value_latest = float(
        market_latest[
            "total_value"
        ].sum()
    )

    avg_price_latest = float(
        market_latest[
            "mean_price"
        ].mean()
    )

    median_price_latest = float(
        market_latest[
            "median_price"
        ].mean()
    )

    rppi_latest = float(
        market_latest[
            "national_rppi"
        ].mean()
    )

    # --------------------------------------------------------
    # Partial year / YTD
    # --------------------------------------------------------

    market_ytd = market[
        market["year"] == PARTIAL_YEAR
    ].copy()

    if market_ytd.empty:

        transactions_ytd = 0
        avg_price_ytd = None
        ytd_period = "No data"

    else:

        transactions_ytd = int(
            market_ytd[
                "transactions"
            ].sum()
        )

        avg_price_ytd = float(
            market_ytd[
                "mean_price"
            ].mean()
        )

        latest_ytd_month = get_latest_month(
            market_ytd
        )

        ytd_period = (
            f"January-"
            f"{latest_ytd_month.strftime('%B')}"
        )

    # --------------------------------------------------------
    # County information
    # --------------------------------------------------------

    county_latest = county[
        county["sale_year"]
        == latest_completed_market_year
    ].copy()

    if county_latest.empty:
        highest_transaction_county = None
        highest_price_county = None
    else:

        highest_transaction_county = (
            county_latest
            .sort_values(
                "transactions",
                ascending=False,
            )
            .iloc[0]
        )

        highest_price_county = (
            county_latest
            .sort_values(
                "mean_price",
                ascending=False,
            )
            .iloc[0]
        )

    # --------------------------------------------------------
    # Planning information
    # --------------------------------------------------------

    planning_completed = planning[
        planning["year"] < PARTIAL_YEAR
    ].copy()

    if planning_completed.empty:

        latest_planning_year = None
        applications_latest = 0
        residential_units_latest = 0

    else:

        latest_planning_year = int(
            planning_completed["year"].max()
        )

        planning_latest = planning_completed[
            planning_completed["year"]
            == latest_planning_year
        ]

        applications_latest = int(
            planning_latest[
                "applications"
            ].sum()
        )

        residential_units_latest = float(
            planning_latest[
                "residential_units"
            ].sum()
        )

    # --------------------------------------------------------
    # Build KPI table
    # --------------------------------------------------------

    kpis = pd.DataFrame(
        [
            {
                "kpi": (
                    f"{latest_completed_market_year} "
                    "Transactions"
                ),
                "value": transactions_latest,
                "unit": "transactions",
            },
            {
                "kpi": (
                    f"{latest_completed_market_year} "
                    "Total Transaction Value"
                ),
                "value": round(
                    total_value_latest,
                    2,
                ),
                "unit": "EUR",
            },
            {
                "kpi": (
                    f"{latest_completed_market_year} "
                    "Average Monthly Mean Price"
                ),
                "value": round(
                    avg_price_latest,
                    2,
                ),
                "unit": "EUR",
            },
            {
                "kpi": (
                    f"{latest_completed_market_year} "
                    "Average Monthly Median Price"
                ),
                "value": round(
                    median_price_latest,
                    2,
                ),
                "unit": "EUR",
            },
            {
                "kpi": (
                    f"{latest_completed_market_year} "
                    "Average RPPI"
                ),
                "value": round(
                    rppi_latest,
                    2,
                ),
                "unit": "index",
            },
            {
                "kpi": (
                    f"{PARTIAL_YEAR} "
                    "YTD Transactions"
                ),
                "value": transactions_ytd,
                "unit": "transactions",
            },
            {
                "kpi": (
                    f"{PARTIAL_YEAR} "
                    "YTD Average Monthly Mean Price"
                ),
                "value": (
                    round(avg_price_ytd, 2)
                    if avg_price_ytd is not None
                    else None
                ),
                "unit": "EUR",
            },
            {
                "kpi": (
                    f"{PARTIAL_YEAR} "
                    "YTD Period"
                ),
                "value": ytd_period,
                "unit": "period",
            },
            {
                "kpi": (
                    "Highest Transaction Volume "
                    f"County {latest_completed_market_year}"
                ),
                "value": (
                    highest_transaction_county[
                        "county"
                    ]
                    if highest_transaction_county
                    is not None
                    else None
                ),
                "unit": "county",
            },
            {
                "kpi": (
                    "Highest Average Price "
                    f"County {latest_completed_market_year}"
                ),
                "value": (
                    highest_price_county[
                        "county"
                    ]
                    if highest_price_county
                    is not None
                    else None
                ),
                "unit": "county",
            },
            {
                "kpi": (
                    f"{latest_planning_year} "
                    "Planning Applications"
                ),
                "value": applications_latest,
                "unit": "applications",
            },
            {
                "kpi": (
                    f"{latest_planning_year} "
                    "Residential Units in Applications"
                ),
                "value": round(
                    residential_units_latest,
                    2,
                ),
                "unit": "units",
            },
        ]
    )

    return kpis


# ============================================================
# SAVE ANALYSIS RESULTS
# ============================================================

def save_analysis_results(
    annual_market: pd.DataFrame,
    market_2026_ytd: pd.DataFrame,
    price_growth: pd.DataFrame,
    county_latest: pd.DataFrame,
    county_price_change: pd.DataFrame,
    property_mix: pd.DataFrame,
    planning_annual: pd.DataFrame,
    planning_authority: pd.DataFrame,
    market_planning_correlation: pd.DataFrame,
    kpis: pd.DataFrame,
) -> None:
    """
    Save all analysis outputs as CSV files.
    """

    outputs = {
        "annual_market_summary.csv": annual_market,
        "market_2026_ytd.csv": market_2026_ytd,
        "price_growth.csv": price_growth,
        "county_market_2025.csv": county_latest,
        "county_price_change_2010_2025.csv": (
            county_price_change
        ),
        "county_property_mix_2025.csv": property_mix,
        "annual_planning_activity.csv": planning_annual,
        "planning_authority_2025.csv": planning_authority,
        "market_planning_correlation.csv": (
            market_planning_correlation
        ),
        "key_kpis.csv": kpis,
    }

    for filename, dataframe in outputs.items():

        output_path = ANALYSIS_DIR / filename

        dataframe.to_csv(
            output_path,
            index=False,
        )

        print(
            f"Saved: {output_path}"
        )


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_analysis_summary(
    annual_market: pd.DataFrame,
    market_2026_ytd: pd.DataFrame,
    county_latest: pd.DataFrame,
    county_price_change: pd.DataFrame,
    planning_annual: pd.DataFrame,
    kpis: pd.DataFrame,
) -> None:
    """
    Print a concise summary of the analysis.
    """

    print("\n")
    print("=" * 70)
    print("IRISH PROPERTY MARKET — ANALYSIS SUMMARY")
    print("=" * 70)

    # --------------------------------------------------------
    # Dataset coverage
    # --------------------------------------------------------

    print("\nDATA COVERAGE")

    if not annual_market.empty:

        print(
            f"- Completed annual data: "
            f"{int(annual_market['year'].min())}-"
            f"{int(annual_market['year'].max())}"
        )

    if not market_2026_ytd.empty:

        print(
            f"- 2026 YTD period: "
            f"{market_2026_ytd.iloc[0]['period']}"
        )

    # --------------------------------------------------------
    # Latest completed year
    # --------------------------------------------------------

    if not annual_market.empty:

        latest = annual_market.iloc[-1]

        latest_year = int(
            latest["year"]
        )

        print("\nLATEST COMPLETED YEAR")

        print(
            f"- Year: {latest_year}"
        )

        print(
            f"- Transactions: "
            f"{int(latest['transactions']):,}"
        )

        print(
            f"- Total transaction value: "
            f"€{latest['total_value']:,.2f}"
        )

        print(
            f"- Average monthly mean price: "
            f"€{latest['avg_monthly_mean_price']:,.2f}"
        )

        print(
            f"- Average monthly median price: "
            f"€{latest['avg_monthly_median_price']:,.2f}"
        )

        print(
            f"- Average RPPI: "
            f"{latest['avg_rppi']:.2f}"
        )

    # --------------------------------------------------------
    # 2026 YTD
    # --------------------------------------------------------

    if not market_2026_ytd.empty:

        ytd = market_2026_ytd.iloc[0]

        print("\n2026 YEAR-TO-DATE")

        print(
            f"- Period: {ytd['period']}"
        )

        print(
            f"- Transactions: "
            f"{int(ytd['transactions']):,}"
        )

        if pd.notna(
            ytd["total_value"]
        ):

            print(
                f"- Total transaction value: "
                f"€{ytd['total_value']:,.2f}"
            )

        if pd.notna(
            ytd["avg_monthly_mean_price"]
        ):

            print(
                f"- Average monthly mean price: "
                f"€{ytd['avg_monthly_mean_price']:,.2f}"
            )

        if pd.notna(
            ytd["avg_monthly_median_price"]
        ):

            print(
                f"- Average monthly median price: "
                f"€{ytd['avg_monthly_median_price']:,.2f}"
            )

        if pd.notna(
            ytd["avg_rppi"]
        ):

            print(
                f"- Average RPPI: "
                f"{ytd['avg_rppi']:.2f}"
            )

    # --------------------------------------------------------
    # County analysis
    # --------------------------------------------------------

    if not county_latest.empty:

        county_year = int(
            county_latest[
                "sale_year"
            ].iloc[0]
        )

        print(
            f"\nCOUNTY MARKET — {county_year}"
        )

        top_transactions = (
            county_latest
            .sort_values(
                "transactions",
                ascending=False,
            )
            .head(5)
        )

        print(
            "\nTop 5 counties by transaction volume:"
        )

        for _, row in top_transactions.iterrows():

            print(
                f"- {row['county']}: "
                f"{int(row['transactions']):,} "
                f"transactions"
            )

        top_prices = (
            county_latest
            .sort_values(
                "mean_price",
                ascending=False,
            )
            .head(5)
        )

        print(
            "\nTop 5 counties by mean price:"
        )

        for _, row in top_prices.iterrows():

            print(
                f"- {row['county']}: "
                f"€{row['mean_price']:,.2f}"
            )

    # --------------------------------------------------------
    # County price change
    # --------------------------------------------------------

    if not county_price_change.empty:

        comparison_year = (
            county_price_change.columns
        )

        price_columns = [
            column
            for column in comparison_year
            if str(column).startswith(
                "mean_price_"
            )
        ]

        target_year = (
            price_columns[-1].replace(
                "mean_price_",
                ""
            )
            if price_columns
            else "latest year"
        )

        print(
            f"\nCOUNTY PRICE CHANGE — "
            f"{BASELINE_YEAR} TO {target_year}"
        )

        top_growth = (
            county_price_change
            .head(5)
        )

        for _, row in top_growth.iterrows():

            print(
                f"- {row['county']}: "
                f"{row['price_change_pct']:.2f}%"
            )

    # --------------------------------------------------------
    # Planning
    # --------------------------------------------------------

    if not planning_annual.empty:

        latest_planning = (
            planning_annual.iloc[-1]
        )

        planning_year = int(
            latest_planning["year"]
        )

        print(
            f"\nPLANNING ACTIVITY — "
            f"{planning_year}"
        )

        print(
            f"- Applications: "
            f"{int(latest_planning['applications']):,}"
        )

        print(
            f"- Granted applications: "
            f"{int(latest_planning['granted_applications']):,}"
        )

        print(
            f"- Refused applications: "
            f"{int(latest_planning['refused_applications']):,}"
        )

        print(
            f"- Residential units: "
            f"{latest_planning['residential_units']:,.0f}"
        )

        if pd.notna(
            latest_planning["grant_rate_pct"]
        ):

            print(
                f"- Grant rate: "
                f"{latest_planning['grant_rate_pct']:.2f}%"
            )

    # --------------------------------------------------------
    # KPI count
    # --------------------------------------------------------

    print(
        f"\nKey KPIs generated: "
        f"{len(kpis)}"
    )

    print("\n")
    print("=" * 70)
    print("ANALYSIS COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(
        f"\nAnalysis files saved to:\n"
        f"{ANALYSIS_DIR}"
    )


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """
    Execute the complete Stage 3 analysis pipeline.
    """

    print("=" * 70)
    print("IRISH PROPERTY MARKET — STAGE 3 ANALYSIS")
    print("=" * 70)

    print(
        "\nConnecting to PostgreSQL..."
    )

    engine = get_engine()

    print(
        "Database connection established."
    )

    # --------------------------------------------------------
    # Load analytical datasets
    # --------------------------------------------------------

    print(
        "\nLoading analytics tables..."
    )

    monthly_market = (
        load_monthly_market(engine)
    )

    county_market = (
        load_county_market(engine)
    )

    planning_activity = (
        load_planning_activity(engine)
    )

    print(
        f"- Monthly market rows: "
        f"{len(monthly_market):,}"
    )

    print(
        f"- County market rows: "
        f"{len(county_market):,}"
    )

    print(
        f"- Planning activity rows: "
        f"{len(planning_activity):,}"
    )

    # --------------------------------------------------------
    # Display source coverage
    # --------------------------------------------------------

    print("\nSOURCE DATA COVERAGE")

    market_start = (
        monthly_market[
            "month_start"
        ].min()
    )

    market_end = (
        monthly_market[
            "month_start"
        ].max()
    )

    planning_start = (
        planning_activity[
            "month_start"
        ].min()
    )

    planning_end = (
        planning_activity[
            "month_start"
        ].max()
    )

    county_start = int(
        county_market[
            "sale_year"
        ].min()
    )

    county_end = int(
        county_market[
            "sale_year"
        ].max()
    )

    print(
        f"- Monthly market: "
        f"{market_start.strftime('%Y-%m')} "
        f"to "
        f"{market_end.strftime('%Y-%m')}"
    )

    print(
        f"- County market: "
        f"{county_start} "
        f"to "
        f"{county_end}"
    )

    print(
        f"- Planning activity: "
        f"{planning_start.strftime('%Y-%m')} "
        f"to "
        f"{planning_end.strftime('%Y-%m')}"
    )

    # --------------------------------------------------------
    # Run analyses
    # --------------------------------------------------------

    print(
        "\nRunning national market analysis..."
    )

    (
        annual_market,
        market_2026_ytd,
    ) = analyse_national_market(
        monthly_market
    )

    print(
        "Running price-growth analysis..."
    )

    price_growth = analyse_price_growth(
        monthly_market
    )

    print(
        "Running county analysis..."
    )

    (
        county_latest,
        county_price_change,
        property_mix,
    ) = analyse_counties(
        county_market
    )

    print(
        "Running planning-activity analysis..."
    )

    (
        planning_annual,
        planning_authority,
    ) = analyse_planning_activity(
        planning_activity
    )

    print(
        "Running market-vs-planning analysis..."
    )

    market_planning_correlation = (
        analyse_market_vs_planning(
            monthly_market,
            planning_activity,
        )
    )

    print(
        "Calculating project KPIs..."
    )

    kpis = calculate_key_kpis(
        monthly_market,
        county_market,
        planning_activity,
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    print(
        "\nSaving analysis results..."
    )

    save_analysis_results(
        annual_market=annual_market,
        market_2026_ytd=market_2026_ytd,
        price_growth=price_growth,
        county_latest=county_latest,
        county_price_change=county_price_change,
        property_mix=property_mix,
        planning_annual=planning_annual,
        planning_authority=planning_authority,
        market_planning_correlation=(
            market_planning_correlation
        ),
        kpis=kpis,
    )

    # --------------------------------------------------------
    # Print summary
    # --------------------------------------------------------

    print_analysis_summary(
        annual_market=annual_market,
        market_2026_ytd=market_2026_ytd,
        county_latest=county_latest,
        county_price_change=county_price_change,
        planning_annual=planning_annual,
        kpis=kpis,
    )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()