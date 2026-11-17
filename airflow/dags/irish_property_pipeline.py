"""Manually triggered orchestration for the Irish property pipeline."""

import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"
PYTHON = shlex.quote(sys.executable)


def python_module_task(task_id: str, module: str) -> BashOperator:
    """Run a project module with the Python used by the Airflow worker."""

    return BashOperator(
        task_id=task_id,
        bash_command=f"{PYTHON} -m {module}",
        cwd=str(PROJECT_ROOT),
    )


with DAG(
    dag_id="irish_property_market_pipeline",
    description="End-to-end Irish property market analytics pipeline",
    start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["irish-property", "analytics", "postgres", "dbt"],
) as dag:
    ppr_ingestion = python_module_task(
        task_id="ppr_ingestion",
        module="src.ppr_ingestion",
    )

    rppi_ingestion = python_module_task(
        task_id="rppi_ingestion",
        module="src.rppi_ingestion",
    )

    planning_ingestion = python_module_task(
        task_id="planning_ingestion",
        module="src.planning_ingestion",
    )

    load_postgres = python_module_task(
        task_id="load_postgres",
        module="src.load_postgres",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="dbt build --profiles-dir .",
        cwd=str(DBT_PROJECT_DIR),
    )

    bigquery_load = python_module_task(
        task_id="bigquery_load",
        module="src.load_bigquery",
    )

    market_analysis = python_module_task(
        task_id="market_analysis",
        module="src.market_analysis",
    )

    validate_analysis = python_module_task(
        task_id="validate_analysis",
        module="src.validate_analysis",
    )

    [
        ppr_ingestion,
        rppi_ingestion,
        planning_ingestion,
    ] >> load_postgres

    load_postgres >> dbt_build >> bigquery_load >> market_analysis
    market_analysis >> validate_analysis
