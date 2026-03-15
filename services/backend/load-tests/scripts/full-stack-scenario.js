// Full-stack scenario load test for the Lotus backend.
//
// Simulates realistic user journeys by combining multiple API calls into
// weighted scenarios that mirror actual frontend usage patterns.
//
// Scenarios:
//   1. new_user_onboarding  (10%) - Registration + first journal
//   2. returning_user       (60%) - Browse journals + write new entry
//   3. read_heavy           (25%) - Read journals only
//   4. oauth_registration   (5%)  - OAuth user creation flow
//
// Usage:
//   k6 run services/backend/load-tests/scripts/full-stack-scenario.js
//   k6 run -e PROFILE=average services/backend/load-tests/scripts/full-stack-scenario.js

import http from "k6/http";
import { check, group, sleep } from "k6";
import { Counter } from "k6/metrics";
import {
  BASE_URL,
  BACKEND_API_KEY,
  defaultThresholds,
  presets,
} from "../lib/config.js";
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
const scenarioRuns = new Counter("scenario_runs");

// ---------- Options ----------
const profile = __ENV.PROFILE || "smoke";
const baseScenario = presets[profile];

// Build a weighted scenario from the base preset. Handles both
// constant-arrival-rate (has `rate`) and ramping-arrival-rate (has
// `startRate` + `stages`) executor types.
function weightedScenario(exec, weight, tags) {
  const s = { ...baseScenario, exec, tags };

  if (s.rate !== undefined) {
    // constant-arrival-rate
    s.rate = Math.max(1, Math.ceil(s.rate * weight));
  }
  if (s.startRate !== undefined) {
    // ramping-arrival-rate
    s.startRate = Math.max(1, Math.ceil(s.startRate * weight));
  }
  if (Array.isArray(s.stages)) {
    s.stages = s.stages.map((stage) => ({
      ...stage,
      target: Math.max(1, Math.ceil(stage.target * weight)),
    }));
  }

  return s;
}

export const options = {
  scenarios: {
    new_user_onboarding: weightedScenario("newUserOnboarding", 0.1, {
      scenario: "new_user_onboarding",
    }),
    returning_user: weightedScenario("returningUser", 0.6, {
      scenario: "returning_user",
    }),
    read_heavy: weightedScenario("readHeavy", 0.25, {
      scenario: "read_heavy",
    }),
    oauth_registration: weightedScenario("oauthRegistration", 0.05, {
      scenario: "oauth_registration",
    }),
  },
  thresholds: {
    ...defaultThresholds,
    "http_req_duration{scenario:new_user_onboarding}": ["p(95)<800"],
    "http_req_duration{scenario:returning_user}": ["p(95)<600"],
    "http_req_duration{scenario:read_heavy}": ["p(95)<400"],
    "http_req_duration{scenario:oauth_registration}": ["p(95)<600"],
  },
};

const headers = {
  "Content-Type": "application/json",
  Authorization: `Bearer ${BACKEND_API_KEY}`,
};

// ---------- Setup: wait for backend readiness ----------
export function setup() {
  waitForReady(BASE_URL);
}

// ---------- Helper: create user and return userId ----------
function createUser() {
  const payload = JSON.stringify({
    email: randomEmail(),
    password: randomPassword(),
  });

  const res = http.post(`${BASE_URL}/v1/users`, payload, { headers });
  if (res.status === 200) {
    const body = res.json();
    return body.user_id || body.userId;
  }
  return null;
}

// ---------- Helper: create journal and return journalId ----------
function createJournal(userId) {
  const payload = JSON.stringify({
    user_id: userId,
    journal_text: randomJournalText(),
    user_mood: randomMood(),
  });

  const res = http.post(`${BASE_URL}/v1/journals`, payload, { headers });
  checkResponse(res, 200, "CreateJournal");
  if (res.status === 200) {
    const body = res.json();
    return body.journal_id || body.journalId;
  }
  return null;
}

// ---------- Scenario 1: New user onboarding (10%) ----------
// Simulates a brand new user: register, write first journal.
export function newUserOnboarding() {
  scenarioRuns.add(1);

  let userId;

  group("Onboarding: register", () => {
    userId = createUser();
    check(userId, {
      "Onboarding: user created": (id) => id !== null,
    });
  });

  if (!userId) return;
  sleep(1); // Simulate user reading the UI

  group("Onboarding: first journal", () => {
    createJournal(userId);
  });
}

// ---------- Scenario 2: Returning user (60%) ----------
// Simulates an existing user: create user (stand-in for login), browse
// journals, write a new entry, browse again.
export function returningUser() {
  scenarioRuns.add(1);

  // Create a user to simulate "logged in" state.
  const userId = createUser();
  if (!userId) return;

  sleep(0.5);

  // Seed a couple of journal entries so reads are non-empty.
  createJournal(userId);
  sleep(0.2);
  createJournal(userId);
  sleep(0.5);

  group("Returning: browse journals page 1", () => {
    const res = http.get(
      `${BASE_URL}/v1/journals?user_id=${userId}&limit=10&offset=0`,
      { headers },
    );
    checkResponse(res, 200, "Browse journals p1");
  });

  sleep(0.3);

  group("Returning: write new journal", () => {
    createJournal(userId);
  });

  sleep(0.5);

  group("Returning: browse journals page 1 (refresh)", () => {
    const res = http.get(
      `${BASE_URL}/v1/journals?user_id=${userId}&limit=10&offset=0`,
      { headers },
    );
    checkResponse(res, 200, "Browse journals refresh");
  });
}

// ---------- Scenario 3: Read-heavy (25%) ----------
// Simulates a user who mostly reads: create user, seed data, then
// repeatedly fetch journals.
export function readHeavy() {
  scenarioRuns.add(1);

  const userId = createUser();
  if (!userId) return;

  // Seed a few entries
  for (let i = 0; i < 3; i++) {
    createJournal(userId);
    sleep(0.1);
  }

  sleep(0.3);

  // Multiple read passes
  for (let page = 0; page < 3; page++) {
    group(`ReadHeavy: journals page ${page}`, () => {
      const res = http.get(
        `${BASE_URL}/v1/journals?user_id=${userId}&limit=10&offset=${page * 10}`,
        { headers },
      );
      checkResponse(res, 200, `Journals page ${page}`);
    });
    sleep(0.2);
  }

  group("ReadHeavy: random string", () => {
    const res = http.get(`${BASE_URL}/v1/util/random-string`, { headers });
    checkResponse(res, 200, "Random string");
  });
}

// ---------- Scenario 4: OAuth registration (5%) ----------
// Simulates a user registering via OAuth provider.
export function oauthRegistration() {
  scenarioRuns.add(1);

  let userId;

  group("OAuth: register", () => {
    const payload = JSON.stringify({
      email: randomEmail(),
      oauth_provider: randomOauthProvider(),
    });

    const res = http.post(`${BASE_URL}/v1/oauth/users`, payload, { headers });
    checkResponse(res, 200, "OAuthRegister");
    if (res.status === 200) {
      const body = res.json();
      userId = body.user_id || body.userId;
    }
  });

  if (!userId) return;
  sleep(0.5);

  group("OAuth: first journal", () => {
    createJournal(userId);
  });

  sleep(0.3);

  group("OAuth: browse journals", () => {
    const res = http.get(
      `${BASE_URL}/v1/journals?user_id=${userId}&limit=10&offset=0`,
      { headers },
    );
    checkResponse(res, 200, "OAuth browse");
  });
}
