// HTTP Gateway load test for the Lotus backend.
//
// Targets the grpc-gateway HTTP endpoints on port 8080 which mirrors
// how the Next.js frontend communicates with the backend.
//
// Usage:
//   # Smoke test (default)
//   k6 run services/backend/load-tests/scripts/http-gateway-load.js
//
//   # Average load
//   k6 run -e PROFILE=average services/backend/load-tests/scripts/http-gateway-load.js
//
//   # Stress test
//   k6 run -e PROFILE=stress services/backend/load-tests/scripts/http-gateway-load.js
//
//   # Override base URL
//   k6 run -e BASE_URL=http://staging:8080 services/backend/load-tests/scripts/http-gateway-load.js

import http from "k6/http";
import { check, group, sleep } from "k6";
import { Trend, Counter } from "k6/metrics";
import { BASE_URL, defaultThresholds, presets } from "../lib/config.js";
import {
  randomEmail,
  randomPassword,
  randomJournalText,
  randomMood,
  randomOauthProvider,
  checkResponse,
  waitForReady,
} from "../lib/helpers.js";

// ---------- Custom metrics ----------
const createUserDuration = new Trend("create_user_duration", true);
const createJournalDuration = new Trend("create_journal_duration", true);
const getJournalsDuration = new Trend("get_journals_duration", true);
const journalsCreated = new Counter("journals_created");

// ---------- Options ----------
const profile = __ENV.PROFILE || "smoke";

export const options = {
  scenarios: {
    default: {
      ...presets[profile],
      exec: "default",
    },
  },
  thresholds: {
    ...defaultThresholds,
    create_user_duration: ["p(95)<600"],
    create_journal_duration: ["p(95)<800"],
    get_journals_duration: ["p(95)<400"],
  },
};

const headers = { "Content-Type": "application/json" };

// ---------- Setup: wait for backend readiness ----------
export function setup() {
  waitForReady(BASE_URL);
}

// ---------- Helpers ----------

/**
 * Log diagnostic info when a response has an unexpected status code.
 */
function logUnexpectedStatus(name, res, expected) {
  if (res.status !== expected) {
    console.warn(
      `${name}: expected ${expected}, got ${res.status} — ${res.body}`,
    );
  }
}

// ---------- Scenario ----------
export default function () {
  let userId;

  // 1. Create a new user
  group("POST /v1/users - create user", () => {
    const payload = JSON.stringify({
      email: randomEmail(),
      password: randomPassword(),
    });

    const res = http.post(`${BASE_URL}/v1/users`, payload, { headers });
    createUserDuration.add(res.timings.duration);

    logUnexpectedStatus("CreateUser", res, 200);
    const ok = checkResponse(res, 200, "CreateUser");
    if (ok) {
      const body = res.json();
      userId = body.user_id || body.userId;
    }
  });

  if (!userId) {
    // If user creation failed, skip remaining steps for this iteration.
    return;
  }

  sleep(0.3);

  // 2. Create a journal entry
  let journalId;
  group("POST /v1/journals - create journal", () => {
    const payload = JSON.stringify({
      user_id: userId,
      journal_text: randomJournalText(),
      user_mood: randomMood(),
    });

    const res = http.post(`${BASE_URL}/v1/journals`, payload, { headers });
    createJournalDuration.add(res.timings.duration);

    logUnexpectedStatus("CreateJournal", res, 200);
    const ok = checkResponse(res, 200, "CreateJournal");
    if (ok) {
      journalsCreated.add(1);
      const body = res.json();
      journalId = body.journal_id || body.journalId;
    }
  });

  sleep(0.3);

  // 3. Fetch journals for the user (with pagination)
  group("GET /v1/journals - list journals", () => {
    const res = http.get(
      `${BASE_URL}/v1/journals?user_id=${userId}&limit=10&offset=0`,
    );
    getJournalsDuration.add(res.timings.duration);

    logUnexpectedStatus("GetJournals", res, 200);
    checkResponse(res, 200, "GetJournals");
    if (res.status === 200) {
      check(res, {
        "GetJournals: has journals array": (r) => {
          const body = r.json();
          return Array.isArray(body.journals);
        },
      });
    }
  });

  sleep(0.3);

  // 4. Utility endpoint (lightweight, good for measuring baseline latency)
  group("GET /v1/util/random-string", () => {
    const res = http.get(`${BASE_URL}/v1/util/random-string`);

    logUnexpectedStatus("GenerateRandomString", res, 200);
    checkResponse(res, 200, "GenerateRandomString");
    if (res.status === 200) {
      check(res, {
        "GenerateRandomString: has random_string field": (r) => {
          const body = r.json();
          return typeof (body.random_string || body.randomString) === "string";
        },
      });
    }
  });
}

// ---------- OAuth user creation (secondary scenario) ----------
// Can be enabled via: k6 run -e INCLUDE_OAUTH=true ...
export function oauthFlow() {
  group("POST /v1/oauth/users - create oauth user", () => {
    const payload = JSON.stringify({
      email: randomEmail(),
      oauth_provider: randomOauthProvider(),
    });

    const res = http.post(`${BASE_URL}/v1/oauth/users`, payload, { headers });
    createUserDuration.add(res.timings.duration);
    checkResponse(res, 200, "CreateUserOauth");
  });
}
