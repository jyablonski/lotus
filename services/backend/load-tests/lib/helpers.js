// Shared helper functions for Lotus backend load tests.

import http from "k6/http";
import { check, sleep } from "k6";
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.4.0/index.js";

// ---------- Data generators ----------

const journalTexts = [
  "Today was a productive day. I managed to finish the report and had a great lunch with colleagues.",
  "Feeling a bit overwhelmed with the workload. Need to prioritize better tomorrow.",
  "Had an amazing morning run. The weather was perfect and I beat my personal record.",
  "Spent the evening reading a new book. It really helped me unwind after a stressful day.",
  "Grateful for the small things today - a warm cup of coffee, sunshine, and good music.",
  "Struggled with focus today. Going to try a different approach to time management tomorrow.",
  "Great conversation with an old friend. It reminded me of what truly matters in life.",
  "Worked on a challenging problem at work and finally cracked it. Feeling accomplished.",
  "Took some time for self-care today. Long bath, meditation, and early bed.",
  "Explored a new neighborhood on my walk. Found a wonderful little cafe I want to revisit.",
];

const moods = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

const oauthProviders = ["github", "google"];

/**
 * Generate a unique email address for a new user.
 */
export function randomEmail() {
  return `loadtest-${uuidv4()}@test.com`;
}

/**
 * Generate a random password that satisfies typical constraints.
 */
export function randomPassword() {
  return `Pass${uuidv4().slice(0, 8)}!`;
}

/**
 * Pick a random journal text from the sample pool.
 */
export function randomJournalText() {
  return journalTexts[Math.floor(Math.random() * journalTexts.length)];
}

/**
 * Pick a random mood score (1-10 as string).
 */
export function randomMood() {
  return moods[Math.floor(Math.random() * moods.length)];
}

/**
 * Pick a random OAuth provider.
 */
export function randomOauthProvider() {
  return oauthProviders[Math.floor(Math.random() * oauthProviders.length)];
}

// ---------- Common checks ----------

/**
 * Assert that an HTTP response has the expected status code and a JSON body.
 */
export function checkResponse(res, expectedStatus, name) {
  const prefix = name ? `${name}: ` : "";
  return check(res, {
    [`${prefix}status is ${expectedStatus}`]: (r) =>
      r.status === expectedStatus,
    [`${prefix}has body`]: (r) => r.body && r.body.length > 0,
  });
}

// ---------- Readiness ----------

/**
 * Poll the backend until it accepts TCP connections and returns any HTTP response.
 * Intended for use in k6 setup() to avoid testing against a server that hasn't
 * started yet (e.g. in Docker Compose where `service_started` only waits for
 * the container process, not the listening socket).
 *
 * Any HTTP status (including 500) counts as "ready" — it means the server is
 * listening and processing requests. A status of 0 means the connection was
 * refused or timed out (server not yet up).
 *
 * @param {string} baseUrl - Base URL of the backend (e.g. http://backend:8080)
 * @param {object} [opts]
 * @param {number} [opts.maxRetries=30]   - Number of retries before giving up
 * @param {number} [opts.intervalSec=2]   - Seconds between retries
 * @param {string} [opts.path=/v1/util/random-string] - Endpoint to probe
 */
export function waitForReady(baseUrl, opts = {}) {
  const maxRetries = opts.maxRetries || 30;
  const intervalSec = opts.intervalSec || 2;
  const path = opts.path || "/v1/util/random-string";
  const url = `${baseUrl}${path}`;

  for (let i = 1; i <= maxRetries; i++) {
    try {
      const res = http.get(url, { timeout: "5s" });
      if (res.status > 0) {
        console.log(
          `Backend ready after ${i} attempt(s) (${url} → ${res.status})`,
        );
        return;
      }
      console.log(
        `Attempt ${i}/${maxRetries}: ${url} → status 0 (connection refused), retrying in ${intervalSec}s …`,
      );
    } catch (e) {
      console.log(
        `Attempt ${i}/${maxRetries}: ${url} → ${e}, retrying in ${intervalSec}s …`,
      );
    }
    sleep(intervalSec);
  }

  throw new Error(`Backend not ready after ${maxRetries} attempts (${url})`);
}
