# Irish Property Market Analytics Platform

An end-to-end data engineering and analytics project for analysing Ireland's residential property market from official public data. The platform combines property transactions, a national price index, and planning-application activity into a reproducible analytical pipeline and a Power BI reporting layer.

## Objective

The project is designed to:

- analyse Irish residential property transactions;
- combine PPR, CSO RPPI, and planning-application data;
- build a production-style data pipeline with defined ingestion, validation, transformation, and warehouse stages; and
- provide analytical outputs through BigQuery and Power BI.

## Architecture

```text
Official Public Data
        |
        v
Python Ingestion
        |
        v
Validation and Cleaning
        |
        v
PostgreSQL
(raw)
        |
        v
dbt Transformations
        |
        v
PostgreSQL
(staging -> analytics)
        |
        v
BigQuery Analytical Warehouse
        |
        v
Power BI Dashboard
```

Python handles ingestion, cleaning, validation, and warehouse loading. PostgreSQL stores the `raw`, `staging`, and `analytics` layers; dbt turns the raw source tables into typed staging tables and analytics marts. BigQuery is the analytical warehouse used by the reporting layer.

Apache Airflow is the orchestration layer in the documented architecture: it coordinates the ingestion, validation, transformation, and publication steps. It is intentionally distinct from Python ingestion and dbt transformations.

## Data Sources

| Source | Purpose |
| --- | --- |
| Residential Property Price Register (PPR) | Property transaction-level analysis. |
| CSO Residential Property Price Index (RPPI) | Independent property-price benchmark for transaction trends. |
| National Planning Applications | Planning and development activity. |

These sources are complementary rather than interchangeable. PPR records completed property transactions, RPPI is an independent price-index benchmark, and planning applications describe development activity rather than property sales or completions.

## Completed Data Scale

| Dataset or output | Completed scale |
| --- | ---: |
| PPR transactions after cleaning | 805,424 |
| Exact duplicate PPR rows removed | 1,079 |
| RPPI records | 20,720 |
| Planning applications | 507,518 |
| Monthly market records | 201 |
| County-market records | 442 |
| Planning-activity records | 4,349 |
| Market/planning correlation metrics | 16 |

## Technology Stack

| Component | Role |
| --- | --- |
| Python | Source ingestion, cleaning, validation, analysis, and loads. |
| PostgreSQL | Layered operational store: `raw`, `staging`, and `analytics`. |
| dbt | SQL transformations from raw source tables to analytics-ready models. |
| Apache Airflow | Pipeline orchestration and scheduling layer. |
| Google BigQuery | Analytical warehouse for curated outputs. |
| Power BI | Interactive reporting and dashboard presentation. |

## Analytical Outputs

The analysis layer produces curated outputs for market and planning analysis, including:

- annual market summaries, price-growth outputs, and year-to-date market metrics;
- county-level market, price-change, and property-mix views;
- annual and planning-authority activity outputs;
- 16 market/planning correlation metrics; and
- a consolidated set of key KPI outputs.

The correlation outputs are reported as descriptive metrics. They do not establish causation.

## Quality Assurance

The completed pipeline recorded **61/61 automated QA checks passed**. The QA coverage verifies expected files and columns, duplicate rows, non-empty outputs, missing values, key transaction reconciliations, county coverage and calculations, planning calculations, and correlation observation counts.

The dbt project contains **7 models** and **27 tests**. Its staging and mart models are documented in `docs/dbt_stage.md`; database loading and validation are documented in `docs/postgresql_stage.md`.

## Power BI Dashboard

The completed dashboard presents transaction and planning KPIs alongside monthly market trends, planning activity, and county-level views. The report is backed by the curated analytical outputs in BigQuery.

Dashboard functional testing confirmed that the Year filter propagates across the KPI cards and supporting visuals. No additional visual changes are required for the completed dashboard.

## Limitations

- The three public sources measure different concepts and may differ in coverage, timing, definitions, and refresh schedules.
- Planning applications are not equivalent to housing completions, property transactions, or confirmed future supply.
- RPPI is an index benchmark and is not a substitute for transaction-level PPR analysis.
- Correlations are descriptive only and should not be interpreted as causal effects.
- County and monthly aggregates can conceal variation within smaller geographic areas or shorter periods.

## Repository Structure

```text
src/                Python ingestion, validation, analysis, and warehouse-load scripts
sql/                PostgreSQL schema, transformation, and validation SQL
dbt/                dbt sources, staging models, marts, macros, and profiles
data/analysis/      Generated analytical outputs and QA report
docs/               PostgreSQL, dbt, and source documentation
```

## Project Status

The data pipeline, analytical outputs, QA checks, BigQuery warehouse load, and Power BI dashboard have been completed. This repository is maintained as a portfolio and educational project using public data.
