import os
from typing import Any

import pandas as pd
import psycopg2
from google.cloud import bigquery


# ============================================================
# CONFIGURATION
# ============================================================

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "172.29.192.1")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "irish_property_market")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

BIGQUERY_PROJECT = os.getenv(
    "BIGQUERY_PROJECT",
    "irish-property-analytics",
)

BIGQUERY_DATASET = os.getenv(
    "BIGQUERY_DATASET",
    "property_analytics",
)

BIGQUERY_LOCATION = os.getenv(
    "BIGQUERY_LOCATION",
    "US",
)


# ============================================================
# SOURCE → TARGET TABLE MAPPING
# ============================================================

TABLE_MAPPING = {
    "analytics.county_market": "mart_county_market",
    "analytics.monthly_market": "mart_monthly_market",
    "analytics.planning_activity": "mart_planning_activity",
    "analytics.property_market_summary": "property_market_summary",
}


# ============================================================
# BIGQUERY SCHEMAS
# ============================================================

BIGQUERY_SCHEMAS = {
    "mart_county_market": [
        bigquery.SchemaField("county", "STRING"),
        bigquery.SchemaField("sale_year", "INTEGER"),
        bigquery.SchemaField("transactions", "INTEGER"),
        bigquery.SchemaField("total_value", "NUMERIC"),
        bigquery.SchemaField("mean_price", "NUMERIC"),
        bigquery.SchemaField("median_price", "NUMERIC"),
        bigquery.SchemaField("new_property_transactions", "INTEGER"),
        bigquery.SchemaField("second_hand_property_transactions", "INTEGER"),
    ],

    "mart_monthly_market": [
        bigquery.SchemaField("year_month", "STRING"),
        bigquery.SchemaField("month_start", "DATE"),
        bigquery.SchemaField("transactions", "INTEGER"),
        bigquery.SchemaField("total_value", "NUMERIC"),
        bigquery.SchemaField("mean_price", "NUMERIC"),
        bigquery.SchemaField("median_price", "NUMERIC"),
        bigquery.SchemaField("national_rppi", "NUMERIC"),
    ],

    "mart_planning_activity": [
        bigquery.SchemaField("planning_authority", "STRING"),
        bigquery.SchemaField("year_month", "STRING"),
        bigquery.SchemaField("month_start", "DATE"),
        bigquery.SchemaField("applications", "INTEGER"),
        bigquery.SchemaField("granted_applications", "INTEGER"),
        bigquery.SchemaField("refused_applications", "INTEGER"),
        bigquery.SchemaField("residential_units", "NUMERIC"),
    ],

    "property_market_summary": [
        bigquery.SchemaField("metric_name", "STRING"),
        bigquery.SchemaField("metric_value", "NUMERIC"),
        bigquery.SchemaField("metric_text", "STRING"),
    ],
}


# ============================================================
# POSTGRESQL CONNECTION
# ============================================================

def create_postgres_connection():
    """Create a PostgreSQL connection."""

    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


# ============================================================
# READ POSTGRES TABLE
# ============================================================

def read_postgres_table(
    connection,
    source_table: str,
) -> pd.DataFrame:
    """Read a PostgreSQL analytics table into a DataFrame."""

    query = f"SELECT * FROM {source_table};"

    with connection.cursor() as cursor:
        cursor.execute(query)

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ]

    return pd.DataFrame(rows, columns=columns)


# ============================================================
# LOAD DATAFRAME INTO BIGQUERY
# ============================================================

def load_to_bigquery(
    client: bigquery.Client,
    dataframe: pd.DataFrame,
    target_table: str,
) -> None:
    """Replace a BigQuery table with the PostgreSQL analytics data."""

    table_id = (
        f"{BIGQUERY_PROJECT}."
        f"{BIGQUERY_DATASET}."
        f"{target_table}"
    )

    schema = BIGQUERY_SCHEMAS[target_table]

    # Ensure date columns are represented correctly.
    for column in ["month_start"]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
            ).dt.date

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"Loading {len(dataframe):,} rows into {table_id}...")

    load_job = client.load_table_from_dataframe(
        dataframe,
        table_id,
        job_config=job_config,
        location=BIGQUERY_LOCATION,
    )

    load_job.result()

    print(
        f"Successfully loaded {len(dataframe):,} rows "
        f"into {target_table}."
    )


# ============================================================
# VERIFY BIGQUERY ROW COUNT
# ============================================================

def verify_bigquery_table(
    client: bigquery.Client,
    target_table: str,
) -> int:
    """Return the row count of a BigQuery table."""

    table_id = (
        f"{BIGQUERY_PROJECT}."
        f"{BIGQUERY_DATASET}."
        f"{target_table}"
    )

    query = f"""
        SELECT COUNT(*) AS row_count
        FROM `{table_id}`
    """

    query_job = client.query(
        query,
        location=BIGQUERY_LOCATION,
    )

    result = list(query_job.result())

    return int(result[0]["row_count"])


# ============================================================
# MAIN PIPELINE
# ============================================================

def main() -> None:
    print("=" * 60)
    print("POSTGRESQL → BIGQUERY WAREHOUSE LOAD")
    print("=" * 60)

    print()
    print("Configuration:")
    print(f"PostgreSQL host: {POSTGRES_HOST}")
    print(f"PostgreSQL database: {POSTGRES_DB}")
    print(f"BigQuery project: {BIGQUERY_PROJECT}")
    print(f"BigQuery dataset: {BIGQUERY_DATASET}")
    print(f"BigQuery location: {BIGQUERY_LOCATION}")

    print()
    print("Connecting to PostgreSQL...")

    postgres_connection = create_postgres_connection()

    print("PostgreSQL connection OK.")

    print()
    print("Connecting to BigQuery...")

    bigquery_client = bigquery.Client(
        project=BIGQUERY_PROJECT,
    )

    print("BigQuery connection OK.")

    try:
        print()
        print("-" * 60)

        for source_table, target_table in TABLE_MAPPING.items():

            print()
            print(
                f"Processing: "
                f"{source_table} → {target_table}"
            )

            # ------------------------------------------------
            # Read PostgreSQL
            # ------------------------------------------------

            dataframe = read_postgres_table(
                postgres_connection,
                source_table,
            )

            postgres_row_count = len(dataframe)

            print(
                f"PostgreSQL rows: "
                f"{postgres_row_count:,}"
            )

            # ------------------------------------------------
            # Load BigQuery
            # ------------------------------------------------

            load_to_bigquery(
                bigquery_client,
                dataframe,
                target_table,
            )

            # ------------------------------------------------
            # Verify BigQuery
            # ------------------------------------------------

            bigquery_row_count = verify_bigquery_table(
                bigquery_client,
                target_table,
            )

            print(
                f"BigQuery rows: "
                f"{bigquery_row_count:,}"
            )

            # ------------------------------------------------
            # Validate counts
            # ------------------------------------------------

            if postgres_row_count != bigquery_row_count:
                raise RuntimeError(
                    f"Row-count mismatch for {target_table}: "
                    f"PostgreSQL={postgres_row_count:,}, "
                    f"BigQuery={bigquery_row_count:,}"
                )

            print(
                f"✓ {target_table}: "
                f"row count verified"
            )

        print()
        print("=" * 60)
        print("BIGQUERY LOAD SUCCESSFUL")
        print("=" * 60)

    finally:
        postgres_connection.close()
        print("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()
