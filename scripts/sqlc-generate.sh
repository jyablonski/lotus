#!/usr/bin/env bash
set -euo pipefail

export PATH="$PATH:$HOME/go/bin"

cd services/backend || exit 1
sqlc generate
