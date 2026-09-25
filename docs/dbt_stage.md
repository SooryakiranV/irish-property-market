# dbt Transformation Stage

The dbt project in `dbt/` transforms the PostgreSQL `raw` schema into typed `staging` tables and analytics-ready marts.

## Current flow

1. Python ingestion creates cleaned CSV files.
2. `src/load_postgres.py` loads the cleaned files into PostgreSQL `raw` tables.
3. dbt reads `raw.*` sources and builds:
   - `staging.ppr_transactions`
   - `staging.rppi_series`
   - `staging.planning_applications`
   - `analytics.monthly_market`
   - `analytics.county_market`
   - `analytics.planning_activity`
   - `analytics.property_market_summary`

## Running dbt locally

From the repository root, load the `.env` settings into the current PowerShell session, then run dbt from the `dbt/` directory:

```powershell
Get-Content .env | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object { $name, $value = $_ -split '=', 2; Set-Item -Path "Env:$name" -Value $value }
Set-Location .\dbt
dbt debug --profiles-dir .
dbt parse --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

The checked-in `profiles.yml` reads PostgreSQL settings from environment variables and does not store secrets.
