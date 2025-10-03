#!/usr/bin/env bash
cd services/backend || exit 1
sqlc generate
