from datetime import datetime
import os

from airflow.decorators import dag, task


@dag(
    dag_id="debug_python_dependencies",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["debug"],
)
def debug_deps_dag():
    @task
    def print_installed_packages():
        print("Starting dependency check...")

        # 'pip freeze' lists all installed packages (excluding standard lib)
        # os.popen allows us to run this shell command from within Python
        stream = os.popen("pip freeze")
        output = stream.read()

        print("\n=== INSTALLED PACKAGES ===")
        print(output)
        print("==========================\n")

    print_installed_packages()


debug_deps_dag()
