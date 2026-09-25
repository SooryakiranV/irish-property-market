"""
Irish Property Market — Stage 4 QA & Validation

Validates Stage 3 analytical outputs against the PostgreSQL
analytics tables.

This script:
    1. Checks Stage 3 CSV files exist.
    2. Checks required columns.
    3. Checks missing values and duplicates.
    4. Reconciles national market totals.
    5. Validates 2026 YTD calculations.
    6. Validates county calculations.
    7. Validates planning calculations.
    8. Validates property-mix percentages.
    9. Validates correlation observations.
   10. Produces a QA report.

No database tables are modified.
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


# ============================================================
# QA RESULT STORAGE
# ============================================================

qa_results = []


def record_check(
    check_name: str,
    status: str,
    details: str,
):
    """Record one QA check."""

    qa_results.append(
        {
            "check_name": check_name,
            "status": status,
            "details": details,
        }
    )

    symbol = "PASS" if status == "PASS" else "FAIL"

    print(
        f"[{symbol}] {check_name} — {details}"
    )


# ============================================================
# FILE DEFINITIONS
# ============================================================

EXPECTED_FILES = {
    "annual_market": "annual_market_summary.csv",
    "market_2026_ytd": "market_2026_ytd.csv",
    "price_growth": "price_growth.csv",
    "county_market": "county_market_2025.csv",
    "county_price_change": "county_price_change_2010_2025.csv",
    "county_property_mix": "county_property_mix_2025.csv",
    "annual_planning": "annual_planning_activity.csv",
    "planning_authority": "planning_authority_2025.csv",
    "market_planning_correlation": (
        "market_planning_correlation.csv"
    ),
    "key_kpis": "key_kpis.csv",
}


# ============================================================
# LOAD STAGE 3 OUTPUTS
# ============================================================

def load_stage3_outputs():
    """Load all Stage 3 CSV outputs."""

    outputs = {}

    for name, filename in EXPECTED_FILES.items():

        path = ANALYSIS_DIR / filename

        if not path.exists():

            record_check(
                "Stage 3 file exists",
                "FAIL",
                f"Missing file: {path}",
            )

        else:

            outputs[name] = pd.read_csv(path)

            record_check(
                f"Stage 3 file exists: {filename}",
                "PASS",
                f"{len(outputs[name]):,} rows",
            )

    return outputs


# ============================================================
# CHECK CSV STRUCTURE
# ============================================================

EXPECTED_COLUMNS = {
    "annual_market": [
        "year",
        "period",
        "transactions",
        "total_value",
        "avg_monthly_mean_price",
        "avg_monthly_median_price",
        "avg_rppi",
    ],
    "market_2026_ytd": [
        "year",
        "period",
        "transactions",
        "total_value",
        "avg_monthly_mean_price",
        "avg_monthly_median_price",
        "avg_rppi",
    ],
    "price_growth": [
        "year",
        "avg_mean_price",
        "avg_median_price",
        "avg_rppi",
        "mean_price_yoy_pct",
        "median_price_yoy_pct",
        "rppi_yoy_pct",
    ],
    "county_market": [
        "county",
        "sale_year",
        "transactions",
        "total_value",
        "mean_price",
        "median_price",
        "new_property_transactions",
        "second_hand_property_transactions",
    ],
    "county_price_change": [
        "county",
        "mean_price_2010",
        "mean_price_2025",
        "price_change_pct",
    ],
    "county_property_mix": [
        "county",
        "sale_year",
        "new_property_transactions",
        "second_hand_property_transactions",
        "total_classified_transactions",
        "new_property_share_pct",
        "second_hand_property_share_pct",
    ],
    "annual_planning": [
        "year",
        "applications",
        "granted_applications",
        "refused_applications",
        "residential_units",
        "grant_rate_pct",
        "refusal_rate_pct",
    ],
    "planning_authority": [
        "planning_authority",
        "applications",
        "granted_applications",
        "refused_applications",
        "residential_units",
        "grant_rate_pct",
        "refusal_rate_pct",
    ],
    "market_planning_correlation": [
        "market_metric",
        "planning_metric",
        "pearson_correlation",
        "observations",
    ],
    "key_kpis": [
        "kpi",
        "value",
        "unit",
    ],
}


def validate_columns(outputs):
    """Check expected CSV columns."""

    for name, expected in EXPECTED_COLUMNS.items():

        if name not in outputs:
            continue

        actual = list(outputs[name].columns)

        missing = [
            column
            for column in expected
            if column not in actual
        ]

        if missing:

            record_check(
                f"Columns: {name}",
                "FAIL",
                f"Missing columns: {missing}",
            )

        else:

            record_check(
                f"Columns: {name}",
                "PASS",
                "All expected columns present",
            )


# ============================================================
# GENERIC DATA QUALITY CHECKS
# ============================================================

def validate_duplicates(outputs):
    """Check duplicate rows."""

    for name, df in outputs.items():

        duplicates = int(
            df.duplicated().sum()
        )

        if duplicates == 0:

            record_check(
                f"Duplicates: {name}",
                "PASS",
                "No duplicate rows",
            )

        else:

            record_check(
                f"Duplicates: {name}",
                "FAIL",
                f"{duplicates:,} duplicate rows",
            )


def validate_empty_outputs(outputs):
    """Check that output files contain data."""

    for name, df in outputs.items():

        if df.empty:

            record_check(
                f"Non-empty output: {name}",
                "FAIL",
                "CSV contains no rows",
            )

        else:

            record_check(
                f"Non-empty output: {name}",
                "PASS",
                f"{len(df):,} rows",
            )


# ============================================================
# DATABASE LOADERS
# ============================================================

def load_monthly_market(engine):

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

    return pd.read_sql(query, engine)


def load_county_market(engine):

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

    return pd.read_sql(query, engine)


def load_planning_activity(engine):

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

    return pd.read_sql(query, engine)


# ============================================================
# NATIONAL MARKET VALIDATION
# ============================================================

def validate_national_market(
    outputs,
    monthly_market,
):
    """Validate 2025 and 2026 national market outputs."""

    monthly_market = monthly_market.copy()

    monthly_market["month_start"] = pd.to_datetime(
        monthly_market["month_start"]
    )

    monthly_market["year"] = (
        monthly_market["month_start"].dt.year
    )

    # --------------------------------------------------------
    # 2025
    # --------------------------------------------------------

    source_2025 = monthly_market[
        monthly_market["year"] == 2025
    ]

    output_2025 = outputs[
        "annual_market"
    ]

    output_2025 = output_2025[
        output_2025["year"] == 2025
    ].iloc[0]

    source_transactions = int(
        source_2025["transactions"].sum()
    )

    output_transactions = int(
        output_2025["transactions"]
    )

    if source_transactions == output_transactions:

        record_check(
            "2025 transaction reconciliation",
            "PASS",
            f"{source_transactions:,} transactions",
        )

    else:

        record_check(
            "2025 transaction reconciliation",
            "FAIL",
            (
                f"Source={source_transactions:,}, "
                f"Output={output_transactions:,}"
            ),
        )

    source_value = round(
        source_2025["total_value"].sum(),
        2,
    )

    output_value = round(
        output_2025["total_value"],
        2,
    )

    if source_value == output_value:

        record_check(
            "2025 transaction-value reconciliation",
            "PASS",
            f"€{source_value:,.2f}",
        )

    else:

        record_check(
            "2025 transaction-value reconciliation",
            "FAIL",
            (
                f"Source=€{source_value:,.2f}, "
                f"Output=€{output_value:,.2f}"
            ),
        )

    # --------------------------------------------------------
    # 2026 YTD
    # --------------------------------------------------------

    source_2026 = monthly_market[
        monthly_market["year"] == 2026
    ]

    output_2026 = outputs[
        "market_2026_ytd"
    ].iloc[0]

    source_transactions_2026 = int(
        source_2026["transactions"].sum()
    )

    output_transactions_2026 = int(
        output_2026["transactions"]
    )

    if (
        source_transactions_2026
        == output_transactions_2026
    ):

        record_check(
            "2026 YTD transaction reconciliation",
            "PASS",
            f"{source_transactions_2026:,} transactions",
        )

    else:

        record_check(
            "2026 YTD transaction reconciliation",
            "FAIL",
            (
                f"Source={source_transactions_2026:,}, "
                f"Output={output_transactions_2026:,}"
            ),
        )

    source_value_2026 = round(
        source_2026["total_value"].sum(),
        2,
    )

    output_value_2026 = round(
        output_2026["total_value"],
        2,
    )

    if source_value_2026 == output_value_2026:

        record_check(
            "2026 YTD transaction-value reconciliation",
            "PASS",
            f"€{source_value_2026:,.2f}",
        )

    else:

        record_check(
            "2026 YTD transaction-value reconciliation",
            "FAIL",
            (
                f"Source=€{source_value_2026:,.2f}, "
                f"Output=€{output_value_2026:,.2f}"
            ),
        )


# ============================================================
# COUNTY VALIDATION
# ============================================================

def validate_counties(
    outputs,
    county_market,
):
    """Validate county-level calculations."""

    county_market = county_market.copy()

    county_2025 = county_market[
        county_market["sale_year"] == 2025
    ].copy()

    output = outputs[
        "county_market"
    ].copy()

    source_counties = set(
        county_2025["county"].dropna()
    )

    output_counties = set(
        output["county"].dropna()
    )

    if source_counties == output_counties:

        record_check(
            "2025 county coverage",
            "PASS",
            f"{len(source_counties)} counties",
        )

    else:

        missing = source_counties - output_counties
        extra = output_counties - source_counties

        record_check(
            "2025 county coverage",
            "FAIL",
            f"Missing={missing}; Extra={extra}",
        )

    # --------------------------------------------------------
    # Property mix
    # --------------------------------------------------------

    mix = outputs[
        "county_property_mix"
    ].copy()

    mix["share_sum"] = (
        mix["new_property_share_pct"]
        + mix["second_hand_property_share_pct"]
    )

    invalid_share = mix[
        (mix["share_sum"] < 99.99)
        | (mix["share_sum"] > 100.01)
    ]

    if invalid_share.empty:

        record_check(
            "County property-mix shares",
            "PASS",
            "Shares sum to approximately 100%",
        )

    else:

        record_check(
            "County property-mix shares",
            "FAIL",
            f"{len(invalid_share)} invalid rows",
        )

    # --------------------------------------------------------
    # Price-change calculation
    # --------------------------------------------------------

    price_change = outputs[
        "county_price_change"
    ].copy()

    expected_change = (
        (
            price_change["mean_price_2025"]
            - price_change["mean_price_2010"]
        )
        / price_change["mean_price_2010"]
        * 100
    ).round(2)

    actual_change = (
        price_change["price_change_pct"]
        .round(2)
    )

    if expected_change.equals(actual_change):

        record_check(
            "County 2010-2025 price-change calculation",
            "PASS",
            "Calculations reconcile",
        )

    else:

        record_check(
            "County 2010-2025 price-change calculation",
            "FAIL",
            "Calculated percentages do not reconcile",
        )


# ============================================================
# PLANNING VALIDATION
# ============================================================

def validate_planning(
    outputs,
    planning_activity,
):
    """Validate planning calculations."""

    planning = planning_activity.copy()

    planning["month_start"] = pd.to_datetime(
        planning["month_start"]
    )

    planning["year"] = (
        planning["month_start"].dt.year
    )

    source_2025 = planning[
        planning["year"] == 2025
    ]

    output = outputs[
        "annual_planning"
    ]

    output_2025 = output[
        output["year"] == 2025
    ].iloc[0]

    # Applications
    source_apps = int(
        source_2025["applications"].sum()
    )

    output_apps = int(
        output_2025["applications"]
    )

    if source_apps == output_apps:

        record_check(
            "2025 planning applications",
            "PASS",
            f"{source_apps:,} applications",
        )

    else:

        record_check(
            "2025 planning applications",
            "FAIL",
            (
                f"Source={source_apps:,}, "
                f"Output={output_apps:,}"
            ),
        )

    # Grant rate
    expected_grant_rate = round(
        (
            output_2025["granted_applications"]
            / output_2025["applications"]
            * 100
        ),
        2,
    )

    actual_grant_rate = round(
        output_2025["grant_rate_pct"],
        2,
    )

    if expected_grant_rate == actual_grant_rate:

        record_check(
            "Planning grant-rate calculation",
            "PASS",
            f"{actual_grant_rate:.2f}%",
        )

    else:

        record_check(
            "Planning grant-rate calculation",
            "FAIL",
            (
                f"Expected={expected_grant_rate:.2f}%, "
                f"Actual={actual_grant_rate:.2f}%"
            ),
        )

    # Refusal rate
    expected_refusal_rate = round(
        (
            output_2025["refused_applications"]
            / output_2025["applications"]
            * 100
        ),
        2,
    )

    actual_refusal_rate = round(
        output_2025["refusal_rate_pct"],
        2,
    )

    if expected_refusal_rate == actual_refusal_rate:

        record_check(
            "Planning refusal-rate calculation",
            "PASS",
            f"{actual_refusal_rate:.2f}%",
        )

    else:

        record_check(
            "Planning refusal-rate calculation",
            "FAIL",
            (
                f"Expected={expected_refusal_rate:.2f}%, "
                f"Actual={actual_refusal_rate:.2f}%"
            ),
        )


# ============================================================
# CORRELATION VALIDATION
# ============================================================

def validate_correlations(
    outputs,
    monthly_market,
    planning_activity,
):
    """Validate correlation observation counts."""

    market = monthly_market.copy()
    planning = planning_activity.copy()

    market["month_start"] = pd.to_datetime(
        market["month_start"]
    )

    planning["month_start"] = pd.to_datetime(
        planning["month_start"]
    )

    planning_monthly = (
        planning
        .groupby(
            "month_start",
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

    merged = market.merge(
        planning_monthly,
        on="month_start",
        how="inner",
    )

    correlation_output = outputs[
        "market_planning_correlation"
    ]

    # --------------------------------------------------------
    # Validate observations for each correlation pair
    # --------------------------------------------------------

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

    failures = []

    for _, row in correlation_output.iterrows():

        market_column = row["market_metric"]
        planning_column = row["planning_metric"]

        expected_observations = (
            merged[
                [
                    market_column,
                    planning_column,
                ]
            ]
            .dropna()
            .shape[0]
        )

        actual_observations = int(
            row["observations"]
        )

        if actual_observations != expected_observations:

            failures.append(
                (
                    market_column,
                    planning_column,
                    expected_observations,
                    actual_observations,
                )
            )

    # --------------------------------------------------------
    # Record validation result
    # --------------------------------------------------------

    if not failures:

        record_check(
            "Correlation observation count",
            "PASS",
            (
                "Observation counts match pairwise "
                "complete-data calculations"
            ),
        )

    else:

        failure_details = "; ".join(
            (
                f"{market_metric} vs {planning_metric}: "
                f"Expected={expected}, Found={actual}"
            )
            for (
                market_metric,
                planning_metric,
                expected,
                actual,
            ) in failures
        )

        record_check(
            "Correlation observation count",
            "FAIL",
            failure_details,
        )


# ============================================================
# MISSING VALUE REVIEW
# ============================================================

def review_missing_values(outputs):

    for name, df in outputs.items():

        missing = int(
            df.isna().sum().sum()
        )

        if missing == 0:

            record_check(
                f"Missing values: {name}",
                "PASS",
                "No missing values",
            )

        else:

            record_check(
                f"Missing values: {name}",
                "PASS",
                (
                    f"{missing} missing values "
                    f"(review required)"
                ),
            )


# ============================================================
# SAVE QA REPORT
# ============================================================

def save_qa_report():

    report = pd.DataFrame(
        qa_results
    )

    output_path = (
        ANALYSIS_DIR / "qa_report.csv"
    )

    report.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nQA report saved to: {output_path}"
    )

    return report


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "IRISH PROPERTY MARKET — STAGE 4 QA"
    )
    print("=" * 70)

    print("\nLoading Stage 3 outputs...")

    outputs = load_stage3_outputs()

    if not outputs:

        print(
            "\nNo Stage 3 outputs available."
        )

        return

    print("\nChecking CSV structure...")

    validate_columns(outputs)

    print("\nChecking duplicate rows...")

    validate_duplicates(outputs)

    print("\nChecking empty outputs...")

    validate_empty_outputs(outputs)

    print("\nReviewing missing values...")

    review_missing_values(outputs)

    print("\nConnecting to PostgreSQL...")

    engine = create_postgres_engine()

    print(
        "Database connection established."
    )

    print("\nLoading source analytics tables...")

    monthly_market = load_monthly_market(
        engine
    )

    county_market = load_county_market(
        engine
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

    print("\nValidating national market...")

    validate_national_market(
        outputs,
        monthly_market,
    )

    print("\nValidating county analysis...")

    validate_counties(
        outputs,
        county_market,
    )

    print("\nValidating planning analysis...")

    validate_planning(
        outputs,
        planning_activity,
    )

    print("\nValidating correlations...")

    validate_correlations(
        outputs,
        monthly_market,
        planning_activity,
    )

    report = save_qa_report()

    failures = (
        report["status"] == "FAIL"
    ).sum()

    print("\n" + "=" * 70)
    print("STAGE 4 QA SUMMARY")
    print("=" * 70)

    print(
        f"\nTotal checks: {len(report)}"
    )

    print(
        f"Passed: "
        f"{(report['status'] == 'PASS').sum()}"
    )

    print(
        f"Failed: {failures}"
    )

    if failures == 0:

        print(
            "\nOVERALL QA STATUS: PASS"
        )

    else:

        print(
            "\nOVERALL QA STATUS: REVIEW REQUIRED"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()