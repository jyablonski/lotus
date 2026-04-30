#!/usr/bin/env bash
set -euo pipefail

# Git/IDE often invoke hooks with a minimal PATH; uv is typically in ~/.local/bin.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to run SQLFluff. Install uv or add it to PATH." >&2
  exit 1
fi

dbt_files=()
for path in "$@"; do
  [[ "$path" == *.sql ]] || continue
  [[ "$path" == services/dbt/* ]] || continue
  [[ "$path" == services/dbt/target/* ]] && continue
  [[ "$path" == services/dbt/dbt_packages/* ]] && continue
  dbt_files+=("${path#services/dbt/}")
done

if [ "${#dbt_files[@]}" -eq 0 ]; then
  exit 0
fi

cd services/dbt
UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" uv run sqlfluff fix \
  --templater jinja \
  --disable-progress-bar \
  "${dbt_files[@]}"
