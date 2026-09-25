# PostgreSQL Integration Stage

This stage loads the existing cleaned project datasets into PostgreSQL:

- PPR transactions
- RPPI series
- Planning Applications

It does not add a new CSO dataset. RPPI is the only CSO-sourced dataset currently used by the pipeline.

## Database

Database name:

```text
irish_property_market
```

Schemas:

```text
raw
staging
analytics
```

## Files

```text
sql/001_create_schemas.sql
sql/002_create_tables.sql
sql/003_build_staging.sql
sql/004_build_analytics.sql
sql/005_create_indexes.sql
sql/validation/database_validation.sql
src/db_config.py
src/load_postgres.py
```

## Required Inputs

These files must exist before loading PostgreSQL:

```text
data/processed/ppr_cleaned.csv
data/processed/rppi_cleaned.csv
data/processed/planning/planning_applications_cleaned.csv
```

## Environment Setup

Create `.env` from `.env.example` and set your PostgreSQL password:

```powershell
Copy-Item .env.example .env
notepad .env
```

Expected PostgreSQL settings:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=irish_property_market
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

## Run The Load

From the project root:

```powershell
cd "C:\Users\M S I\irish-property-market"
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-postgres.txt
python .\src\load_postgres.py
```

## Validate In PostgreSQL

If `psql` is not already on your PATH, add PostgreSQL 17 first:

```powershell
$env:Path += ";C:\Program Files\PostgreSQL\17\bin"
```

Then run:

```powershell
psql -U postgres -d irish_property_market -f .\sql\validation\database_validation.sql
```

The validation output should show populated `raw`, `staging`, and `analytics` tables. The `raw` and `staging` row counts for each source should match.

## Next Stage

Airflow should be added later, after this database stage is stable and validated.
