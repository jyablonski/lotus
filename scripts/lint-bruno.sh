#!/usr/bin/env bash
# Lint Bruno collection for auth hygiene.
set -euo pipefail

BRUNO_DIR="$(git rev-parse --show-toplevel)/bruno"
ERRORS=0

# Endpoints that are intentionally unauthenticated (basename only).
AUTH_NONE_ALLOWLIST="health.bru root.bru"

# 1. Check for auth: none outside the allowlist.
while IFS= read -r -d '' f; do
  base=$(basename "$f")
  # Skip folder.bru, collection.bru, and environment files.
  [[ "$base" == "folder.bru" || "$base" == "collection.bru" ]] && continue
  [[ "$f" == */environments/* ]] && continue

  if grep -q "auth: none" "$f"; then
    if echo "$AUTH_NONE_ALLOWLIST" | grep -qw "$base"; then
      continue
    fi
    echo "ERROR: auth: none in non-allowlisted file: $f"
    echo "       Use 'auth: inherit' or add to AUTH_NONE_ALLOWLIST in scripts/lint-bruno.sh"
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$BRUNO_DIR" -name "*.bru" -print0)

# 2. Check for hardcoded Authorization headers in endpoint files.
while IFS= read -r -d '' f; do
  base=$(basename "$f")
  [[ "$base" == "folder.bru" || "$base" == "collection.bru" ]] && continue
  [[ "$f" == */environments/* ]] && continue

  if grep -qi "Authorization:" "$f"; then
    echo "ERROR: hardcoded Authorization header in $f"
    echo "       Use 'auth: inherit' and let folder.bru supply the token."
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$BRUNO_DIR" -name "*.bru" -print0)

# 3. Check that every folder containing endpoint .bru files has a folder.bru.
while IFS= read -r dir; do
  # Count non-folder, non-environment .bru files in this directory only (not recursive).
  endpoint_count=$(find "$dir" -maxdepth 1 -name "*.bru" \
    ! -name "folder.bru" ! -name "collection.bru" | wc -l)
  [[ "$endpoint_count" -eq 0 ]] && continue

  if [[ ! -f "$dir/folder.bru" ]]; then
    echo "ERROR: folder missing folder.bru: $dir"
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$BRUNO_DIR" -mindepth 1 -maxdepth 2 -type d ! -name "environments")

if [[ "$ERRORS" -gt 0 ]]; then
  echo ""
  echo "Bruno lint failed with $ERRORS error(s)."
  exit 1
fi

echo "Bruno lint passed."
