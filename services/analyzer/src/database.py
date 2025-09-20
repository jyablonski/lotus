import logging
import os
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def substitute_env_vars(yaml_content: dict[str, str]) -> None:
    for key, value in yaml_content.items():
        if isinstance(value, str):
            yaml_content[key] = os.path.expandvars(value)
        elif isinstance(value, dict):
            substitute_env_vars(value)


def load_yaml_with_env(filename: str) -> Any:
    path = Path(filename)
    with path.open() as file:
        yaml_content = yaml.safe_load(file)
        substitute_env_vars(yaml_content)
        return yaml_content


def sql_connection(
    user: str, password: str, host: str, database: str, schema: str, port: int = 5432
) -> Engine:
    """SQL Connection Function

    Args:
        user (str): Database User

        password (str): Database password

        host (str): Database Host IP

        database (str): Database to connect to

        schema (str): The Schema in the DB to connect to.

        port (int): Port to connect to the DB

    Returns:
        SQL Engine variable to a specified schema in the DB
    """
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
        connect_args={"options": f"-csearch_path={schema}"},
        # defining schema to connect to
        echo=False,
    )
    logging.info(f"SQL Engine created for {schema}")
    return engine


env = load_yaml_with_env("config.yaml")[os.environ.get("ENV_TYPE", "dev")]

engine = sql_connection(
    user=env["user"],
    password=env["pass"],
    host=env["host"],
    database=env["database"],
    schema=env["schema"],
    port=env["port"],
)

# separate database sessions for different users essentially.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()
