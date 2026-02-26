#!/usr/bin/env bash
set -euo pipefail

# Generate Bruno collection files from OpenAPI specs.
#
# Steps:
#   1. Run buf generate (which produces swagger files via protoc-gen-openapiv2)
#   2. Export the FastAPI OpenAPI spec from the analyzer service
#   3. Convert both specs to Bruno .bru files

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Generating backend OpenAPI specs (buf generate)..."
cd "$REPO_ROOT/services/backend" && buf generate

echo "==> Exporting analyzer OpenAPI spec..."
cd "$REPO_ROOT/services/analyzer" && uv run python "$REPO_ROOT/scripts/export-analyzer-openapi.py" "$REPO_ROOT/services/analyzer/openapi.json"

echo "==> Converting OpenAPI specs to Bruno files..."
python3 "$REPO_ROOT/scripts/generate-bruno.py"

echo "==> Done. Bruno files updated in bruno/"
