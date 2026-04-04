#!/usr/bin/env bash
# Lint Bruno collections for auth hygiene.
set -euo pipefail

BRUNO_DIR="$(git rev-parse --show-toplevel)/bruno"
COLLECTIONS=("backend" "analyzer")
ERRORS=0

# Endpoint .bru files that are intentionally unauthenticated (basename only).
AUTH_NONE_ALLOWLIST="health.bru root.bru"

for svc in "${COLLECTIONS[@]}"; do
  collection_dir="$BRUNO_DIR/$svc"

  # 1. Each collection must have collection.bru and folder.bru.
  if [[ ! -f "$collection_dir/collection.bru" ]]; then
    echo "ERROR: missing collection.bru in $collection_dir"
    ERRORS=$((ERRORS + 1))
  fi
  if [[ ! -f "$collection_dir/folder.bru" ]]; then
    echo "ERROR: missing folder.bru in $collection_dir"
    ERRORS=$((ERRORS + 1))
  fi

  # 2. Check endpoint files for auth: none outside the allowlist.
  while IFS= read -r -d '' f; do
    base=$(basename "$f")
    [[ "$base" == "collection.bru" ]] && continue
    [[ "$f" == */environments/* ]] && continue

    if grep -q "auth: none" "$f"; then
      if echo "$AUTH_NONE_ALLOWLIST" | grep -qw "$base"; then
        continue
      fi
      echo "ERROR: auth: none in non-allowlisted file: $f"
      echo "       Use 'auth: inherit' or add to AUTH_NONE_ALLOWLIST in scripts/lint-bruno.sh"
      ERRORS=$((ERRORS + 1))
    fi
  done < <(find "$collection_dir" -maxdepth 1 -name "*.bru" -print0)

  # 3. Check for hardcoded Authorization headers in endpoint files.
  while IFS= read -r -d '' f; do
    base=$(basename "$f")
    [[ "$base" == "collection.bru" ]] && continue
    [[ "$f" == */environments/* ]] && continue

    if grep -qi "Authorization:" "$f"; then
      echo "ERROR: hardcoded Authorization header in $f"
      echo "       Use 'auth: inherit' and let collection.bru supply the token."
      ERRORS=$((ERRORS + 1))
    fi
  done < <(find "$collection_dir" -maxdepth 1 -name "*.bru" -print0)
done

if [[ "$ERRORS" -gt 0 ]]; then
  echo ""
  echo "Bruno lint failed with $ERRORS error(s)."
  exit 1
fi

echo "Bruno lint passed."
