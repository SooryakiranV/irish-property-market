# Airflow orchestration

## DAG behavior

`airflow/dags/irish_property_pipeline.py` defines the manually triggered DAG `irish_property_market_pipeline`. It does not run on a timer and does not backfill scheduled intervals. Only one DAG run may be active at a time because the database load replaces project tables.

The task order is:

```text
ppr_ingestion ─────┐
rppi_ingestion ────┼─> load_postgres -> dbt_build -> bigquery_load -> market_analysis -> validate_analysis
planning_ingestion ┘
```

The DAG locates the project relative to its own file and uses the Python interpreter running the Airflow worker. Each Python task runs a project module from the repository root. The dbt task runs from `dbt/`.

## Runtime requirements

Airflow runs on Linux or WSL2, not directly on Windows. The project modules and Airflow tasks need to share a Python environment containing the project dependencies. Apache Airflow core is intentionally separate from `requirements.txt` because it needs a version- and Python-specific constraints file. `requirements-airflow.txt` pins the Standard provider used by `BashOperator`; that provider requires Airflow 2.11.0 or newer.

For a new Linux or WSL2 environment, install Airflow core with its matching official constraints first. This example uses Airflow 3.4.0 and Python 3.11:

```sh
AIRFLOW_VERSION=3.4.0
PYTHON_VERSION=3.11
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
python -m pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
python -m pip install "apache-airflow==${AIRFLOW_VERSION}" -r requirements-airflow.txt -r requirements.txt -r requirements-postgres.txt
python -m pip check
```

If Airflow is already installed, use its exact version in the second command instead of `3.4.0`. Keep the provider compatible with that Airflow version. Airflow's [installation guide](https://airflow.apache.org/docs/apache-airflow/stable/installation/installing-from-pypi.html) explains why core should be installed with matching constraints and pinned when adding providers or project packages.

From the project root, point Airflow at this DAG folder before starting its scheduler and webserver:

```sh
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/airflow/dags"
```

Create `.env` from `.env.example` and configure the PostgreSQL connection, `BIGQUERY_PROJECT`, `BIGQUERY_DATASET`, and `BIGQUERY_LOCATION`. Set `GOOGLE_APPLICATION_CREDENTIALS` to a service-account key file stored outside the repository; the dbt BigQuery profile uses this key-file authentication method. Never commit `.env` or credential files.

## Safe validation and execution

Validate the DAG without running its tasks:

```sh
python -m compileall -q airflow/dags
airflow dags list-import-errors
airflow dags list | grep irish_property_market_pipeline
```

The ingestion tasks need the source datasets and network access. The PostgreSQL loader truncates this project's raw, staging, and analytics tables before reloading them. The BigQuery loader uses `WRITE_TRUNCATE` for its four target tables. A real DAG run therefore needs valid inputs, database/cloud access, and agreement that replacing those tables is intended. These external steps were not run as part of code validation.
