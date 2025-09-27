#!/usr/bin/env bash
set -euo pipefail

cd services/backend || exit 1
buf generate
