# Irish Property Market Analytics Platform

An end-to-end data engineering and analytics project analysing Ireland's residential property market using official Irish public data sources.

## Project Status

🚧 In development

## Technology Stack

- Python
- SQL
- PostgreSQL
- dbt
- Apache Airflow
- Google BigQuery
- Power BI
- GitHub Actions

## Data Sources

- Residential Property Price Register (PPR)
- Residential Property Price Index (RPPI)
- National Planning Applications

## Project Objective

The project will transform raw Irish public data into a reproducible analytical pipeline:

Data → ETL → Data Validation → PostgreSQL → dbt → BigQuery → Power BI

## Current Database Stage

The PostgreSQL stage loads the cleaned PPR, RPPI and Planning Applications datasets into the `irish_property_market` database.

Run it after the cleaned CSV files have been created:

```powershell
python .\src\load_postgres.py
```

Validation queries are available in:

```text
sql/validation/database_validation.sql
```

## Disclaimer

This project is for portfolio and educational purposes. Findings will be based on analysis of the underlying datasets and will not be fabricated or inferred before the analysis is performed.

## dbt Transformation Stage

The dbt project is located in `dbt/`. It reads the PostgreSQL `raw` schema and builds the typed `staging` schema plus analytics marts used by the later BigQuery and Power BI phases.

After the PostgreSQL raw load succeeds, run:

```powershell
Get-Content .env | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object { $name, $value = $_ -split '=', 2; Set-Item -Path "Env:$name" -Value $value }
Set-Location .\dbt
dbt debug --profiles-dir .
dbt parse --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

See `docs/dbt_stage.md` for the current dbt model layout.
