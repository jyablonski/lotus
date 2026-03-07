# Contract Testing Design

## Overview

Add Pact consumer-driven contract tests across the three core services (Frontend, Backend, Analyzer) to catch breaking API changes, document service contracts as living documentation, and enable independent deploys.

## Service Boundaries

Two service boundaries need contract tests:

1. **Frontend (consumer) -> Backend Gateway (provider)** - HTTP/JSON over REST
2. **Backend (consumer) -> Analyzer (provider)** - HTTP/JSON over REST

## Approach

Pact consumer-driven contract testing. Each consumer writes tests defining what it expects from the provider. Those expectations are saved as Pact files (JSON). Each provider verifies it satisfies those expectations. A Docker Pact Broker centralizes the contracts.

## Contracts

### Frontend -> Backend (6 interactions)

| Consumer Call | Method | Path | Request | Response |
|---|---|---|---|---|
| Create journal | POST | `/v1/journals` | `user_id`, `journal_text`, `user_mood` (string) | `journalId` |
| Get journals | GET | `/v1/journals?user_id=X&limit=N&offset=N` | query params | `journals[]`, `totalCount` (string), `hasMore` |
| Get user | GET | `/v1/users?email=X` | query param | `userId`, `email`, `role`, `timezone`, `createdAt`, `updatedAt` |
| Create OAuth user | POST | `/v1/oauth/users` | `email`, `oauth_provider` | `userId` |
| Update timezone | PATCH | `/v1/users/{id}/timezone` | `timezone` | `userId`, `timezone`, `updatedAt` |
| Get feature flags | GET | `/v1/feature-flags?user_role=X` | query param | `flags[].name`, `flags[].isActive` |

### Backend -> Analyzer (2 interactions)

| Consumer Call | Method | Path | Request | Response |
|---|---|---|---|---|
| Trigger sentiment | PUT | `/v1/journals/{id}/sentiment` | `{"force_reanalyze": false}` | 2xx with SentimentResponse body |
| Trigger topics | POST | `/v1/journals/{id}/openai/topics` | `{"force_reanalyze": false}` | 204 No Content |

## Technology

- **Frontend (TypeScript)**: `@pact-foundation/pact` (PactV3)
- **Backend (Go)**: `github.com/pact-foundation/pact-go/v2`
- **Analyzer (Python)**: `pact-python` (provider verification only)
- **Pact Broker**: `pactfoundation/pact-broker` Docker image + PostgreSQL

## File Structure

```
services/
  frontend/
    __tests__/contract/
      journalConsumer.pact.test.ts
      userConsumer.pact.test.ts
      featureFlagConsumer.pact.test.ts
  backend/
    internal/grpc/
      contract_test/
        analyzer_consumer_test.go
        backend_provider_test.go
  analyzer/
    tests/contract/
      test_analyzer_provider.py
docker/
  docker-compose-local.yaml  (add pact-broker service)
  bootstrap/
    03-pact-broker.sql        (create pact_broker database)
```

## Infrastructure

Add Pact Broker to docker-compose-local.yaml with a `pact` profile, using the existing PostgreSQL instance with a dedicated `pact_broker` database.
