#!/usr/bin/env bash
set -euo pipefail

export PATH="$PATH:$HOME/go/bin"

cd services/backend || exit 1

echo "Generating mocks..."

# Generate Querier mock from sqlc-generated interface
moq -out internal/mocks/querier_mock.go -pkg mocks ./internal/db Querier

# Generate HTTPDoer mock for external HTTP calls
moq -out internal/mocks/http_client_mock.go -pkg mocks ./internal/inject HTTPDoer

echo "Mocks generated successfully."
