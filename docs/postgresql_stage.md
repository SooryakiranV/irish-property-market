# PostgreSQL Data Warehouse Stage

## Purpose

PostgreSQL provides the core relational data layer for the Irish Property Market Analytics Platform.

The database separates the pipeline into three logical schemas:

- `raw` — source data loaded from the ingestion layer
- `staging` — cleaned and standardised data produced by dbt
- `analytics` — analytical marts used by downstream analysis and BigQuery

## Raw Layer

The `raw` schema stores the ingested source datasets:

- `raw.ppr_transactions`
- `raw.rppi_series`
- `raw.planning_applications`

The raw layer preserves the source-oriented structure before analytical transformations.

## Staging Layer

The staging layer is built using dbt.

The staging models standardise fields, data types, dates and analytical flags while preserving the underlying source information.

The main staging models are:

- `stg_ppr_transactions`
- `stg_rppi_series`
- `stg_planning_applications`

## Analytics Layer

The analytics layer contains the transformed datasets used for analysis:

- `county_market`
- `monthly_market`
- `planning_activity`
- `market_planning_correlation`
- `property_market_summary`

These models provide the aggregated outputs required for market, county, planning and relationship analysis.

## Data Quality

The PostgreSQL stage was validated through automated checks covering:

- Row counts
- Required fields
- Dates
- Transaction prices
- County coverage
- Analytical aggregates
- Planning metrics
- Correlation observation counts

The final pipeline QA completed with:

**61 checks passed, 0 failed.**

## Downstream Flow

PostgreSQL is the transformation and relational data layer of the pipeline.

The DAG in `airflow/dags/irish_property_pipeline.py` orchestrates the flow:

Airflow: Python ingestion
→ PostgreSQL raw
→ dbt staging and analytics
→ BigQuery analytical warehouse
→ Power BI dashboard

The DAG is manually triggered. Its PostgreSQL reload truncates this project's raw, staging, and analytics tables. Its BigQuery load replaces the mapped tables. See [`airflow.md`](airflow.md) for dependencies, configuration, safe validation, and execution effects.

## Project Status

The PostgreSQL stage is complete and integrated into the end-to-end analytics pipeline.
