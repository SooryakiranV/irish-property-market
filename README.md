# Irish Property Market Analytics

A data engineering and analytics project that brings together Irish property transaction, price-index, and planning data.

## Results and project status

- 7 dbt models and 27 dbt tests
- 61/61 automated QA checks passing
- PostgreSQL and BigQuery data layers
- Power BI dashboard

![Pipeline architecture](docs/architecture.png)

## Data and flow

The project uses the Residential Property Price Register, CSO Residential Property Price Index, and national planning-application data.

Python scripts ingest and validate the sources. PostgreSQL holds the raw, staging, and analytics layers. dbt builds the analytics models. Curated tables are loaded into BigQuery for the Power BI dashboard.

## Run

The repository contains the Python scripts, dbt project, generated analysis files, and Power BI report. It does not include a populated PostgreSQL database or Google Cloud credentials.

Create a local environment and install the dependencies:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-postgres.txt
cp .env.example .env
```

On Windows PowerShell, activate with `\.venv\Scripts\Activate.ps1`. Configure the local database and Google Cloud credential path in `.env`. Place the required raw source tables in PostgreSQL before running the dbt models.

Generate dbt documentation:

```sh
dbt deps --project-dir dbt --profiles-dir dbt
dbt docs generate --project-dir dbt --profiles-dir dbt --target dev
```

Build the BigQuery tables only after configuring BigQuery credentials and location:

```sh
python src/load_bigquery.py
```

The loader replaces its target tables. Cloud operations may incur charges.

Open `Irish_Property_Market_Dashboard.pbix` in Power BI Desktop to view the dashboard.

## Topics

irish-property, data-engineering, dbt, postgresql, bigquery, power-bi
