from pathlib import Path

import pandas as pd
from sqlalchemy import Text, text
from sqlalchemy.engine import Engine

from .db_config import create_postgres_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

DATASETS = {
    "ppr_transactions": PROCESSED_DATA_DIR / "ppr_cleaned.csv",
    "rppi_series": PROCESSED_DATA_DIR / "rppi_cleaned.csv",
    "planning_applications": (
        PROCESSED_DATA_DIR
        / "planning"
        / "planning_applications_cleaned.csv"
    ),
}

SETUP_SQL_FILES = [
    SQL_DIR / "001_create_schemas.sql",
    SQL_DIR / "002_create_tables.sql",
]

BUILD_SQL_FILES = [
    SQL_DIR / "003_build_staging.sql",
    SQL_DIR / "004_build_analytics.sql",
    SQL_DIR / "005_create_indexes.sql",
]


def validate_input_files() -> None:
    """Ensure all cleaned datasets exist before loading PostgreSQL."""

    missing_files = [
        path
        for path in DATASETS.values()
        if not path.exists()
    ]

    if missing_files:
        missing = "\n".join(str(path) for path in missing_files)
        raise FileNotFoundError(
            "PostgreSQL load cannot start because these cleaned "
            f"datasets are missing:\n{missing}"
        )


def execute_sql_file(engine: Engine, sql_file: Path) -> None:
    """Execute one project SQL file."""

    print(f"Running SQL: {sql_file.relative_to(PROJECT_ROOT)}")

    sql = sql_file.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(sql))


def reset_database_tables(engine: Engine) -> None:
    """Clear project tables so each load is reproducible."""

    print("Clearing existing raw, staging, and analytics tables...")

    sql = """
        TRUNCATE TABLE
            raw.ppr_transactions,
            raw.rppi_series,
            raw.planning_applications,
            staging.ppr_transactions,
            staging.rppi_series,
            staging.planning_applications,
            analytics.monthly_market,
            analytics.county_market,
            analytics.planning_activity,
            analytics.property_market_summary
        RESTART IDENTITY;
    """

    with engine.begin() as connection:
        connection.exec_driver_sql(sql)


def load_csv_to_raw_table(
    engine: Engine,
    table_name: str,
    csv_file: Path,
    chunk_size: int = 50_000,
) -> int:
    """Load a CSV file into a raw PostgreSQL table as text."""

    print(f"Loading {csv_file.relative_to(PROJECT_ROOT)} into raw.{table_name}...")

    row_count = 0

    for chunk in pd.read_csv(
        csv_file,
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
        low_memory=False,
    ):
        dtype = {
            column: Text()
            for column in chunk.columns
        }

        chunk.to_sql(
            table_name,
            engine,
            schema="raw",
            if_exists="append",
            index=False,
            dtype=dtype,
            method="multi",
            chunksize=1_000,
        )

        row_count += len(chunk)
        print(f"  loaded {row_count:,} rows")

    return row_count


def print_row_counts(engine: Engine) -> None:
    """Print row counts for the loaded database tables."""

    row_count_sql = text(
        """
        SELECT 'raw.ppr_transactions' AS table_name, count(*) AS row_count
        FROM raw.ppr_transactions
        UNION ALL
        SELECT 'staging.ppr_transactions', count(*)
        FROM staging.ppr_transactions
        UNION ALL
        SELECT 'raw.rppi_series', count(*)
        FROM raw.rppi_series
        UNION ALL
        SELECT 'staging.rppi_series', count(*)
        FROM staging.rppi_series
        UNION ALL
        SELECT 'raw.planning_applications', count(*)
        FROM raw.planning_applications
        UNION ALL
        SELECT 'staging.planning_applications', count(*)
        FROM staging.planning_applications
        UNION ALL
        SELECT 'analytics.monthly_market', count(*)
        FROM analytics.monthly_market
        UNION ALL
        SELECT 'analytics.county_market', count(*)
        FROM analytics.county_market
        UNION ALL
        SELECT 'analytics.planning_activity', count(*)
        FROM analytics.planning_activity
        ORDER BY table_name;
        """
    )

    with engine.connect() as connection:
        results = connection.execute(row_count_sql).fetchall()

    print()
    print("=" * 60)
    print("POSTGRESQL LOAD SUMMARY")
    print("=" * 60)

    for table_name, row_count in results:
        print(f"{table_name}: {row_count:,}")


def main() -> None:
    print("=" * 60)
    print("POSTGRESQL DATABASE LOAD")
    print("=" * 60)

    validate_input_files()

    engine = create_postgres_engine()

    for sql_file in SETUP_SQL_FILES:
        execute_sql_file(engine, sql_file)

    reset_database_tables(engine)

    for table_name, csv_file in DATASETS.items():
        load_csv_to_raw_table(engine, table_name, csv_file)

    for sql_file in BUILD_SQL_FILES:
        execute_sql_file(engine, sql_file)

    print_row_counts(engine)

    print()
    print("=" * 60)
    print("POSTGRESQL LOAD COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
