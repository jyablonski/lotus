"""Export the FastAPI OpenAPI spec to JSON without starting the server.

This script imports the FastAPI app and dumps its OpenAPI schema to a JSON file.
It must be run from the analyzer service directory with its dependencies available,
e.g. via `uv run` from services/analyzer/.

Usage:
    cd services/analyzer && uv run python ../../scripts/export-analyzer-openapi.py <output_path>
"""

from __future__ import annotations

import json

# Mock heavy dependencies that aren't needed for schema generation.
# FastAPI builds the OpenAPI spec from route decorators and Pydantic models,
# so we don't need actual ML clients, database connections, or MLflow.
import os
import sys
from unittest.mock import MagicMock

# Ensure the analyzer service root is on sys.path so `src` resolves.
_analyzer_root = os.path.join(os.path.dirname(__file__), "..", "services", "analyzer")
_analyzer_root = os.path.abspath(_analyzer_root)
if _analyzer_root not in sys.path:
    sys.path.insert(0, _analyzer_root)

for mod in [
    "mlflow",
    "mlflow.pyfunc",
    "mlflow.tracking",
    "mlflow.store",
    "instructor",
    "openai",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# Satisfy the module-level ANALYZER_API_KEY guard in src/main.py without
# needing a real key — we only import the app to extract its OpenAPI schema.
os.environ.setdefault("ANALYZER_API_KEY", "schema-export-placeholder")

from src.main import app  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output_path>", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    schema = app.openapi()

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2, default=str)

    print(f"Exported analyzer OpenAPI spec to {output_path}")


if __name__ == "__main__":
    main()
