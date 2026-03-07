# Contract Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Pact consumer-driven contract tests across Frontend, Backend, and Analyzer services to catch breaking API changes, document service contracts, and enable independent deploys.

**Architecture:** Each consumer service writes Pact tests defining what it expects from its provider. Pact files are published to a Docker Pact Broker. Each provider verifies it satisfies those expectations. Two boundaries: Frontend->Backend (6 interactions) and Backend->Analyzer (2 interactions).

**Tech Stack:** @pact-foundation/pact (TypeScript), pact-go/v2 (Go), pact-python (Python), pactfoundation/pact-broker (Docker)

---

## Task 1: Add Pact Broker Infrastructure

**Files:**
- Modify: `docker/db/01-bootstrap.sql` (add `CREATE DATABASE pact_broker;` at top)
- Modify: `docker/docker-compose-local.yaml` (add pact-broker service)
- Modify: `Makefile` (add pact targets)

**Step 1: Add pact_broker database to bootstrap SQL**

Add this line after the existing `CREATE DATABASE` statements at the top of `docker/db/01-bootstrap.sql`:

```sql
CREATE DATABASE pact_broker;
```

This goes right after `CREATE DATABASE feast;` (line 3).

**Step 2: Add pact-broker service to docker-compose**

Add the following service to `docker/docker-compose-local.yaml`, after the `redisinsight` service:

```yaml
  pact-broker:
    image: pactfoundation/pact-broker:latest
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/pact_broker"
      PACT_BROKER_BASIC_AUTH_USERNAME: "pact"
      PACT_BROKER_BASIC_AUTH_PASSWORD: "pact"
      PACT_BROKER_LOG_LEVEL: "INFO"
    depends_on:
      - postgres
    profiles:
      - pact
```

**Step 3: Add Makefile targets**

Add to `Makefile` before the `help` target:

```makefile
.PHONY: pact-broker-up
pact-broker-up: ## Start the Pact Broker
	@docker compose -f docker/docker-compose-local.yaml --profile pact up -d pact-broker

.PHONY: pact-broker-down
pact-broker-down: ## Stop the Pact Broker
	@docker compose -f docker/docker-compose-local.yaml --profile pact down pact-broker
```

**Step 4: Verify pact broker starts**

Run: `make start-postgres && sleep 3 && make pact-broker-up`

Then: `curl -u pact:pact http://localhost:9292/`

Expected: JSON response with Pact Broker API links.

**Step 5: Commit**

```bash
git add docker/db/01-bootstrap.sql docker/docker-compose-local.yaml Makefile
git commit -m "feat: add Pact Broker infrastructure for contract testing"
```

---

## Task 2: Frontend Consumer Tests - Install Dependencies and Setup

**Files:**
- Modify: `services/frontend/package.json` (add pact dependency)
- Create: `services/frontend/__tests__/contract/pactSetup.ts`
- Modify: `services/frontend/jest.config.js` (exclude contract tests from default run)

**Step 1: Install @pact-foundation/pact**

Run from `services/frontend/`:
```bash
npm install --save-dev @pact-foundation/pact
```

**Step 2: Create Pact test setup helper**

Create `services/frontend/__tests__/contract/pactSetup.ts`:

```typescript
import path from "path";
import { PactV3 } from "@pact-foundation/pact";

export const PROVIDER_NAME = "LotusBackend";
export const CONSUMER_NAME = "LotusFrontend";
export const PACT_DIR = path.resolve(__dirname, "../../pacts");

export function createPact(): PactV3 {
  return new PactV3({
    consumer: CONSUMER_NAME,
    provider: PROVIDER_NAME,
    dir: PACT_DIR,
  });
}
```

**Step 3: Add contract test script to package.json**

Add to the `"scripts"` section of `services/frontend/package.json`:

```json
"test:contract": "jest --testPathPattern='__tests__/contract' --runInBand",
"test:contract:publish": "npx pact-broker publish ./pacts --consumer-app-version=$(git rev-parse --short HEAD) --broker-base-url=http://localhost:9292 --broker-username=pact --broker-password=pact"
```

**Step 4: Exclude contract tests from default Jest run**

In `services/frontend/jest.config.js`, add `"<rootDir>/__tests__/contract/"` to the `testPathIgnorePatterns` array:

```js
testPathIgnorePatterns: [
  "<rootDir>/.next/",
  "<rootDir>/node_modules/",
  "<rootDir>/__tests__/__mocks__/",
  "<rootDir>/e2e/",
  "<rootDir>/__tests__/contract/",
],
```

**Step 5: Commit**

```bash
git add services/frontend/package.json services/frontend/package-lock.json services/frontend/__tests__/contract/pactSetup.ts services/frontend/jest.config.js
git commit -m "feat: add Pact consumer test setup for frontend"
```

---

## Task 3: Frontend Consumer Test - Journal Interactions

**Files:**
- Create: `services/frontend/__tests__/contract/journalConsumer.pact.test.ts`

**Step 1: Write the journal consumer contract test**

Create `services/frontend/__tests__/contract/journalConsumer.pact.test.ts`:

```typescript
import { MatchersV3 } from "@pact-foundation/pact";
import { createPact } from "./pactSetup";

const { like, eachLike, string } = MatchersV3;

const provider = createPact();

describe("Frontend -> Backend: Journal API Contract", () => {
  describe("POST /v1/journals - Create Journal", () => {
    it("creates a journal entry and returns the journal ID", async () => {
      await provider
        .given("a user exists")
        .uponReceiving("a request to create a journal")
        .withRequest({
          method: "POST",
          path: "/v1/journals",
          headers: { "Content-Type": "application/json" },
          body: {
            user_id: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
            journal_text: like("Today was a great day!"),
            user_mood: like("8"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            journalId: like("123"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(`${mockServer.url}/v1/journals`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: "a91b114d-b3de-4fe6-b162-039c9850c06b",
            journal_text: "Today was a great day!",
            user_mood: "8",
          }),
        });

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(data.journalId).toBeDefined();
        expect(typeof data.journalId).toBe("string");
      });
    });
  });

  describe("GET /v1/journals - Get Journals", () => {
    it("returns paginated journal entries for a user", async () => {
      await provider
        .given("a user has journal entries")
        .uponReceiving("a request to get journals with pagination")
        .withRequest({
          method: "GET",
          path: "/v1/journals",
          query: {
            user_id: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
            limit: like("10"),
            offset: like("0"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            journals: eachLike({
              journalId: like("1"),
              userId: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
              journalText: like("Today was a great day!"),
              userMood: like("8"),
              createdAt: like("2026-01-15T10:00:00Z"),
            }),
            totalCount: like("5"),
            hasMore: like(false),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/journals?user_id=a91b114d-b3de-4fe6-b162-039c9850c06b&limit=10&offset=0`,
          {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();

        // Verify response shape matches what frontend expects
        expect(data.journals).toBeInstanceOf(Array);
        expect(data.journals.length).toBeGreaterThan(0);

        const journal = data.journals[0];
        expect(typeof journal.journalId).toBe("string");
        expect(typeof journal.userId).toBe("string");
        expect(typeof journal.journalText).toBe("string");
        expect(typeof journal.userMood).toBe("string"); // Backend returns string, frontend parseInt's it
        expect(typeof journal.createdAt).toBe("string");

        // totalCount is returned as a string by the gRPC gateway
        expect(typeof data.totalCount).toBe("string");
        expect(typeof data.hasMore).toBe("boolean");
      });
    });
  });
});
```

**Step 2: Run the test to verify it passes and generates a pact file**

Run from `services/frontend/`:
```bash
npm run test:contract
```

Expected: Tests pass, pact file created at `services/frontend/pacts/LotusFrontend-LotusBackend.json`.

**Step 3: Commit**

```bash
git add services/frontend/__tests__/contract/journalConsumer.pact.test.ts
git commit -m "feat: add journal consumer contract tests for frontend"
```

---

## Task 4: Frontend Consumer Test - User and OAuth Interactions

**Files:**
- Create: `services/frontend/__tests__/contract/userConsumer.pact.test.ts`

**Step 1: Write the user consumer contract test**

Create `services/frontend/__tests__/contract/userConsumer.pact.test.ts`:

```typescript
import { MatchersV3 } from "@pact-foundation/pact";
import { createPact } from "./pactSetup";

const { like, string } = MatchersV3;

const provider = createPact();

describe("Frontend -> Backend: User API Contract", () => {
  describe("GET /v1/users - Get User by Email", () => {
    it("returns user details for a given email", async () => {
      await provider
        .given("a user with email exists")
        .uponReceiving("a request to get user by email")
        .withRequest({
          method: "GET",
          path: "/v1/users",
          query: {
            email: like("test@example.com"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            userId: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
            email: like("test@example.com"),
            role: like("Consumer"),
            timezone: like("UTC"),
            createdAt: like("2026-01-15T10:00:00Z"),
            updatedAt: like("2026-01-15T10:00:00Z"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/users?email=test@example.com`,
          {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(typeof data.userId).toBe("string");
        expect(typeof data.email).toBe("string");
        expect(typeof data.role).toBe("string");
        expect(typeof data.timezone).toBe("string");
        expect(typeof data.createdAt).toBe("string");
        expect(typeof data.updatedAt).toBe("string");
      });
    });
  });

  describe("POST /v1/oauth/users - Create OAuth User", () => {
    it("creates an OAuth user and returns the user ID", async () => {
      await provider
        .given("no user with this email exists")
        .uponReceiving("a request to create an OAuth user")
        .withRequest({
          method: "POST",
          path: "/v1/oauth/users",
          headers: { "Content-Type": "application/json" },
          body: {
            email: like("newuser@example.com"),
            oauth_provider: like("github"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            userId: like("b91b114d-b3de-4fe6-b162-039c9850c06b"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(`${mockServer.url}/v1/oauth/users`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: "newuser@example.com",
            oauth_provider: "github",
          }),
        });

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(typeof data.userId).toBe("string");
      });
    });
  });

  describe("PATCH /v1/users/{userId}/timezone - Update Timezone", () => {
    it("updates user timezone and returns updated data", async () => {
      const userId = "a91b114d-b3de-4fe6-b162-039c9850c06b";

      await provider
        .given("a user exists")
        .uponReceiving("a request to update user timezone")
        .withRequest({
          method: "PATCH",
          path: `/v1/users/${userId}/timezone`,
          headers: { "Content-Type": "application/json" },
          body: {
            timezone: like("America/New_York"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            userId: like(userId),
            timezone: like("America/New_York"),
            updatedAt: like("2026-01-15T10:00:00Z"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/users/${userId}/timezone`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ timezone: "America/New_York" }),
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(typeof data.userId).toBe("string");
        expect(typeof data.timezone).toBe("string");
        expect(typeof data.updatedAt).toBe("string");
      });
    });
  });
});
```

**Step 2: Run the test**

Run from `services/frontend/`:
```bash
npm run test:contract
```

Expected: All tests pass.

**Step 3: Commit**

```bash
git add services/frontend/__tests__/contract/userConsumer.pact.test.ts
git commit -m "feat: add user consumer contract tests for frontend"
```

---

## Task 5: Frontend Consumer Test - Feature Flags

**Files:**
- Create: `services/frontend/__tests__/contract/featureFlagConsumer.pact.test.ts`

**Step 1: Write the feature flag consumer contract test**

Create `services/frontend/__tests__/contract/featureFlagConsumer.pact.test.ts`:

```typescript
import { MatchersV3 } from "@pact-foundation/pact";
import { createPact } from "./pactSetup";

const { like, eachLike } = MatchersV3;

const provider = createPact();

describe("Frontend -> Backend: Feature Flag API Contract", () => {
  describe("GET /v1/feature-flags - Get Feature Flags", () => {
    it("returns feature flags for a user role", async () => {
      await provider
        .given("feature flags exist")
        .uponReceiving("a request to get feature flags for a role")
        .withRequest({
          method: "GET",
          path: "/v1/feature-flags",
          query: {
            user_role: like("Consumer"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            flags: eachLike({
              name: like("dark_mode"),
              isActive: like(true),
            }),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/feature-flags?user_role=Consumer`,
          {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(data.flags).toBeInstanceOf(Array);
        expect(data.flags.length).toBeGreaterThan(0);

        const flag = data.flags[0];
        expect(typeof flag.name).toBe("string");
        expect(typeof flag.isActive).toBe("boolean");
      });
    });
  });
});
```

**Step 2: Run the test**

Run from `services/frontend/`:
```bash
npm run test:contract
```

Expected: All contract tests pass. Pact file at `services/frontend/pacts/LotusFrontend-LotusBackend.json` now contains all 6 interactions.

**Step 3: Commit**

```bash
git add services/frontend/__tests__/contract/featureFlagConsumer.pact.test.ts
git commit -m "feat: add feature flag consumer contract tests for frontend"
```

---

## Task 6: Backend Consumer Tests - Install pact-go and Setup

**Files:**
- Modify: `services/backend/go.mod` (add pact-go dependency)
- Create: `services/backend/internal/grpc/contract_test/analyzer_consumer_test.go`

**Step 1: Install pact-go CLI and library**

The pact-go v2 library requires the Pact FFI native library. Install it:

Run from `services/backend/`:
```bash
go get github.com/pact-foundation/pact-go/v2@latest
```

Then install the native Pact libraries:
```bash
go run github.com/pact-foundation/pact-go/v2/installer
```

**Step 2: Write the analyzer consumer contract test**

Create directory and file `services/backend/internal/grpc/contract_test/analyzer_consumer_test.go`:

```go
package contract_test

import (
	"fmt"
	"io"
	"net/http"
	"strings"
	"testing"

	"github.com/pact-foundation/pact-go/v2/consumer"
	"github.com/pact-foundation/pact-go/v2/matchers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestBackendAnalyzerContract_TriggerSentiment(t *testing.T) {
	mockProvider, err := consumer.NewV3Pact(consumer.MockHTTPProviderConfig{
		Consumer: "LotusBackend",
		Provider: "LotusAnalyzer",
		PactDir:  "../../../pacts",
	})
	require.NoError(t, err)

	err = mockProvider.
		AddInteraction().
		Given("a journal entry exists in the analyzer database").
		UponReceiving("a request to trigger sentiment analysis").
		WithRequest("PUT", "/v1/journals/123/sentiment", func(b *consumer.V3RequestBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(map[string]interface{}{
				"force_reanalyze": matchers.Like(false),
			})
		}).
		WillRespondWith(200, func(b *consumer.V3ResponseBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(map[string]interface{}{
				"id":               matchers.Like(1),
				"journal_id":       matchers.Like(123),
				"sentiment":        matchers.Like("positive"),
				"confidence":       matchers.Like(0.85),
				"confidence_level": matchers.Like("high"),
				"is_reliable":      matchers.Like(true),
				"ml_model_version": matchers.Like("v1.0.0"),
				"created_at":       matchers.Like("2026-01-15T10:00:00Z"),
			})
		}).
		ExecuteTest(t, func(config consumer.MockServerConfig) error {
			url := fmt.Sprintf("http://%s:%d/v1/journals/123/sentiment", config.Host, config.Port)

			body := strings.NewReader(`{"force_reanalyze":false}`)
			req, err := http.NewRequest("PUT", url, body)
			if err != nil {
				return err
			}
			req.Header.Set("Content-Type", "application/json")

			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)

			respBody, err := io.ReadAll(resp.Body)
			if err != nil {
				return err
			}
			assert.Contains(t, string(respBody), "sentiment")

			return nil
		})

	require.NoError(t, err)
}

func TestBackendAnalyzerContract_TriggerTopics(t *testing.T) {
	mockProvider, err := consumer.NewV3Pact(consumer.MockHTTPProviderConfig{
		Consumer: "LotusBackend",
		Provider: "LotusAnalyzer",
		PactDir:  "../../../pacts",
	})
	require.NoError(t, err)

	err = mockProvider.
		AddInteraction().
		Given("a journal entry exists in the analyzer database").
		UponReceiving("a request to trigger OpenAI topic extraction").
		WithRequest("POST", "/v1/journals/123/openai/topics", func(b *consumer.V3RequestBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(map[string]interface{}{
				"force_reanalyze": matchers.Like(false),
			})
		}).
		WillRespondWith(204).
		ExecuteTest(t, func(config consumer.MockServerConfig) error {
			url := fmt.Sprintf("http://%s:%d/v1/journals/123/openai/topics", config.Host, config.Port)

			body := strings.NewReader(`{"force_reanalyze":false}`)
			req, err := http.NewRequest("POST", url, body)
			if err != nil {
				return err
			}
			req.Header.Set("Content-Type", "application/json")

			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 204, resp.StatusCode)
			return nil
		})

	require.NoError(t, err)
}
```

**Step 3: Run the test to verify it passes and generates a pact file**

Run from `services/backend/`:
```bash
go test ./internal/grpc/contract_test/ -v -run TestBackendAnalyzerContract
```

Expected: Tests pass, pact file created at `services/backend/pacts/LotusBackend-LotusAnalyzer.json`.

**Step 4: Commit**

```bash
git add services/backend/go.mod services/backend/go.sum services/backend/internal/grpc/contract_test/
git commit -m "feat: add backend consumer contract tests for analyzer API"
```

---

## Task 7: Backend Provider Verification - Verify Frontend Contract

**Files:**
- Create: `services/backend/internal/grpc/contract_test/backend_provider_test.go`

This test verifies that the backend satisfies the frontend's contract. It requires the pact file generated by the frontend in Task 3-5. It uses a real gRPC gateway server with mocked database.

**Step 1: Write the provider verification test**

Create `services/backend/internal/grpc/contract_test/backend_provider_test.go`:

```go
package contract_test

import (
	"testing"

	"github.com/pact-foundation/pact-go/v2/provider"
)

func TestBackendSatisfiesFrontendContract(t *testing.T) {
	// This test verifies the backend satisfies the frontend consumer contract.
	// It uses the pact file generated by the frontend consumer tests.
	//
	// To run this test:
	// 1. First run frontend consumer tests: cd services/frontend && npm run test:contract
	// 2. Then run this test with a running backend: go test ./internal/grpc/contract_test/ -v -run TestBackendSatisfiesFrontendContract
	//
	// For CI, use the Pact Broker instead of local files:
	// Set PACT_BROKER_URL, PACT_BROKER_USERNAME, PACT_BROKER_PASSWORD env vars.

	verifier := provider.NewVerifier()

	err := verifier.VerifyProvider(t, provider.VerifyRequest{
		ProviderBaseURL: "http://localhost:8080", // Running backend gateway
		Provider:        "LotusBackend",

		// Option A: Verify from local pact files (for local development)
		PactFiles: []string{
			"../../../frontend/pacts/LotusFrontend-LotusBackend.json",
		},

		// Option B: Verify from broker (for CI) - uncomment and set env vars:
		// BrokerURL:      os.Getenv("PACT_BROKER_URL"),
		// BrokerUsername:  os.Getenv("PACT_BROKER_USERNAME"),
		// BrokerPassword:  os.Getenv("PACT_BROKER_PASSWORD"),
		// PublishVerificationResults: true,
		// ProviderVersion:            os.Getenv("GIT_COMMIT"),

		// State handlers set up test data for each provider state
		StateHandlers: map[string]provider.StateHandlerFunc{
			"a user exists": func(setup bool, s provider.ProviderStateV3) (provider.ProviderStateV3Response, error) {
				// The bootstrap SQL already seeds test users
				return nil, nil
			},
			"a user has journal entries": func(setup bool, s provider.ProviderStateV3) (provider.ProviderStateV3Response, error) {
				// The bootstrap SQL already seeds journal entries
				return nil, nil
			},
			"a user with email exists": func(setup bool, s provider.ProviderStateV3) (provider.ProviderStateV3Response, error) {
				return nil, nil
			},
			"no user with this email exists": func(setup bool, s provider.ProviderStateV3) (provider.ProviderStateV3Response, error) {
				return nil, nil
			},
			"feature flags exist": func(setup bool, s provider.ProviderStateV3) (provider.ProviderStateV3Response, error) {
				return nil, nil
			},
		},
	})

	if err != nil {
		t.Fatal("Provider verification failed:", err)
	}
}
```

**Step 2: Run the provider test (requires running backend)**

This is an integration test that requires a running backend with database. Run with:

```bash
# Start postgres and backend first
make start-postgres
# Wait for postgres, then start backend (or use tilt)

# Then run the provider verification
cd services/backend
go test ./internal/grpc/contract_test/ -v -run TestBackendSatisfiesFrontendContract -tags=integration
```

Expected: Provider verifies all 6 frontend consumer interactions.

**Step 3: Commit**

```bash
git add services/backend/internal/grpc/contract_test/backend_provider_test.go
git commit -m "feat: add backend provider verification for frontend contract"
```

---

## Task 8: Analyzer Provider Verification - Install pact-python and Setup

**Files:**
- Modify: `services/analyzer/pyproject.toml` (add pact-python dev dependency)
- Create: `services/analyzer/tests/contract/__init__.py`
- Create: `services/analyzer/tests/contract/test_analyzer_provider.py`

**Step 1: Add pact-python dependency**

Run from `services/analyzer/`:
```bash
uv add --dev pact-python
```

**Step 2: Create contract test directory**

```bash
mkdir -p services/analyzer/tests/contract
touch services/analyzer/tests/contract/__init__.py
```

**Step 3: Write the analyzer provider verification test**

Create `services/analyzer/tests/contract/test_analyzer_provider.py`:

```python
"""
Analyzer provider contract verification tests.

These tests verify the Analyzer service satisfies the contract expected
by the Backend service (LotusBackend consumer).

To run:
    1. Generate pact files: cd services/backend && go test ./internal/grpc/contract_test/ -v -run TestBackendAnalyzerContract
    2. Start analyzer dependencies: make ci-analyzer-up
    3. Start the analyzer: cd services/analyzer && uv run uvicorn src.main:app --port 8083
    4. Run verification: cd services/analyzer && uv run pytest tests/contract/ -v

For CI, use the Pact Broker instead of local files.
"""

import subprocess

import pytest


@pytest.fixture(scope="module")
def pact_verifier():
    """Return the path to the pact verifier CLI or skip if not available."""
    # pact-python installs a pact-verifier CLI tool
    try:
        result = subprocess.run(
            ["pact-verifier", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return "pact-verifier"
    except FileNotFoundError:
        pass

    pytest.skip("pact-verifier CLI not found. Install with: uv add --dev pact-python")


def test_analyzer_satisfies_backend_contract(pact_verifier):
    """Verify the Analyzer satisfies the Backend's consumer contract.

    This test requires:
    - A running Analyzer service at http://localhost:8083
    - The pact file from backend consumer tests at services/backend/pacts/
    """
    result = subprocess.run(
        [
            pact_verifier,
            "--provider-base-url=http://localhost:8083",
            "--pact-url=../../backend/pacts/LotusBackend-LotusAnalyzer.json",
            "--provider-states-setup-url=http://localhost:8083/v1/pact/provider-states",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    assert result.returncode == 0, f"Provider verification failed:\n{result.stdout}\n{result.stderr}"
```

**Step 4: Add a provider states endpoint to the analyzer (for test setup)**

Create `services/analyzer/src/routers/v1/pact_states.py`:

```python
"""Provider state handler for Pact contract verification.

This endpoint is only used during contract testing to set up
the appropriate state in the analyzer before verification runs.
"""

import logging
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# Only register this router when running contract tests
if os.environ.get("PACT_TESTING", "false").lower() == "true":

    @router.post("/pact/provider-states")
    def handle_provider_state(body: dict, db: Session = Depends(get_db)):
        """Handle provider state setup for Pact verification."""
        state = body.get("state", "")
        action = body.get("action", "setup")

        logger.info(f"Pact provider state: {state} (action={action})")

        if state == "a journal entry exists in the analyzer database":
            if action == "setup":
                # Insert a test journal if it doesn't exist
                from src.models.journals import Journals

                existing = db.query(Journals).filter(Journals.id == 123).first()
                if not existing:
                    journal = Journals(
                        id=123,
                        user_id="a91b114d-b3de-4fe6-b162-039c9850c06b",
                        journal_text="This is a test journal for contract testing.",
                        mood_score=7,
                    )
                    db.add(journal)
                    db.commit()
            elif action == "teardown":
                from src.models.journals import Journals

                db.query(Journals).filter(Journals.id == 123).delete()
                db.commit()

        return {"status": "ok"}
```

**Step 5: Conditionally register the pact states router**

In the analyzer's router setup, the pact_states router should be conditionally included. Add to `services/analyzer/src/routers/v1/__init__.py`:

```python
import os

from fastapi import APIRouter

from .cache import router as cache_router
from .journal_sentiments import router as journal_sentiments_router
from .journal_topics import router as journal_topics_router
from .journal_topics_openai import router as journal_topics_openai_router

v1_router = APIRouter()

v1_router.include_router(journal_topics_router, tags=["topics"])
v1_router.include_router(journal_sentiments_router, tags=["sentiments"])
v1_router.include_router(journal_topics_openai_router, tags=["openai_topics"])
v1_router.include_router(cache_router, tags=["cache"])

# Pact contract testing support (only enabled via env var)
if os.environ.get("PACT_TESTING", "false").lower() == "true":
    from .pact_states import router as pact_states_router

    v1_router.include_router(pact_states_router, tags=["pact"])
```

**Step 6: Commit**

```bash
git add services/analyzer/pyproject.toml services/analyzer/uv.lock services/analyzer/tests/contract/ services/analyzer/src/routers/v1/pact_states.py services/analyzer/src/routers/v1/__init__.py
git commit -m "feat: add analyzer provider verification for backend contract"
```

---

## Task 9: Add .gitignore for Pact Files and pacts/ Directories

**Files:**
- Modify: `.gitignore` or create service-level `.gitignore` files

**Step 1: Add pact output directories to gitignore**

The pact JSON files are generated artifacts and should not be committed. Add to root `.gitignore`:

```
# Pact contract test output
services/frontend/pacts/
services/backend/pacts/
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add pact output directories to gitignore"
```

---

## Task 10: Add CI Workflow for Contract Tests

**Files:**
- Create: `.github/workflows/contract-tests.yaml`

**Step 1: Write the CI workflow**

Create `.github/workflows/contract-tests.yaml`:

```yaml
name: Contract Tests

on:
  pull_request:
    paths:
      - 'services/frontend/**'
      - 'services/backend/**'
      - 'services/analyzer/**'

jobs:
  frontend-consumer:
    name: Frontend Consumer Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: services/frontend/package-lock.json
      - run: npm ci
      - run: npm run test:contract
      - uses: actions/upload-artifact@v4
        with:
          name: frontend-pacts
          path: services/frontend/pacts/
          retention-days: 1

  backend-consumer:
    name: Backend Consumer Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: services/backend/go.mod
      - name: Install Pact FFI
        run: go run github.com/pact-foundation/pact-go/v2/installer
      - run: go test ./internal/grpc/contract_test/ -v -run TestBackendAnalyzerContract
      - uses: actions/upload-artifact@v4
        with:
          name: backend-pacts
          path: services/backend/pacts/
          retention-days: 1
```

**Step 2: Commit**

```bash
git add .github/workflows/contract-tests.yaml
git commit -m "feat: add CI workflow for contract tests"
```

---

## Summary

After completing all 10 tasks, the contract testing setup provides:

1. **Pact Broker** running in Docker for centralized contract management
2. **Frontend consumer tests** covering all 6 API interactions with the backend
3. **Backend consumer tests** covering both analyzer API calls (sentiment + topics)
4. **Backend provider verification** that validates the backend satisfies the frontend's contract
5. **Analyzer provider verification** that validates the analyzer satisfies the backend's contract
6. **CI workflow** that runs consumer tests on every PR

### Running Contract Tests Locally

```bash
# 1. Start infrastructure
make start-postgres && sleep 3 && make pact-broker-up

# 2. Run frontend consumer tests (generates pact files)
cd services/frontend && npm run test:contract

# 3. Run backend consumer tests (generates pact files)
cd services/backend && go test ./internal/grpc/contract_test/ -v -run TestBackendAnalyzerContract

# 4. Publish pacts to broker
cd services/frontend && npm run test:contract:publish

# 5. Verify backend satisfies frontend contract (requires running backend)
cd services/backend && go test ./internal/grpc/contract_test/ -v -run TestBackendSatisfiesFrontendContract

# 6. Verify analyzer satisfies backend contract (requires running analyzer)
cd services/analyzer && PACT_TESTING=true uv run pytest tests/contract/ -v
```
