# Airflow

This project runs Apache Airflow using Astronomer (Astro CLI). It bundles the core Airflow scheduler, webserver, and database into a managed container environment with additional quality-of-life developer tools.

## Project Structure

- `dags/`: Your workflows go here. (e.g., `example_dag.py`).
- `Dockerfile`: Defines the version of the Astro Runtime (Airflow) to use.
- `requirements.txt`: Python dependencies (e.g., `pandas`, `snowflake-connector-python`).
  - _Note:_ These are automatically installed into your Airflow environment at build time.
- `packages.txt`: OS-level dependencies (e.g., `libpq-dev`).
  - _Note:_ These are also automatically installed alongside your Python packages.
- `airflow_settings.yaml`: Local-only configuration for Connections, Variables, and Pools. These reset if you wipe the environment.
- `include/`: storage for non-DAG code, SQL files, or data static files you need to access within your DAGs.
- `plugins/`: Custom Airflow plugins and hooks.

## Quick Start

1.  Start Airflow: `astro dev start`
2.  Access UI: [http://localhost:8080](http://localhost:8080) (User: `admin` / Pass: `admin`)
3.  To stop Airflow: `astro dev stop`
