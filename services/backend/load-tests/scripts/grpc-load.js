// Direct gRPC load test for the Lotus backend.
//
// Tests the gRPC server on port 50051 directly, bypassing the HTTP gateway.
// This is useful for measuring raw gRPC performance and testing endpoints
// that have no HTTP mapping (e.g. TriggerJournalAnalysis).
//
// Usage:
//   # Smoke test (default) — run from repo root
//   k6 run services/backend/load-tests/scripts/grpc-load.js
//
//   # Average load
//   k6 run -e PROFILE=average services/backend/load-tests/scripts/grpc-load.js
//
//   # Override gRPC address
//   k6 run -e GRPC_ADDR=staging:50051 services/backend/load-tests/scripts/grpc-load.js
//
//   # Docker (protos and third_party mounted separately)
//   k6 run -e PROTO_ROOT=/ -e THIRD_PARTY_ROOT=/third_party /scripts/grpc-load.js

import grpc from "k6/net/grpc";
import { check, group, sleep } from "k6";
import { Trend, Counter } from "k6/metrics";
import {
  GRPC_ADDR,
  BASE_URL,
  defaultThresholds,
  presets,
} from "../lib/config.js";
import {
  randomEmail,
  randomPassword,
  randomJournalText,
  randomMood,
  waitForReady,
} from "../lib/helpers.js";

// ---------- gRPC client ----------
const client = new grpc.Client();

// Load proto files.
// PROTO_ROOT — directory containing the proto/ tree (default: services/backend)
// THIRD_PARTY_ROOT — directory containing vendored google/api protos
//                    (default: services/backend/load-tests/third_party)
// In Docker both are mounted at the container root (/ and /third_party).
const protoRoot = __ENV.PROTO_ROOT || "services/backend";
const thirdPartyRoot =
  __ENV.THIRD_PARTY_ROOT || "services/backend/load-tests/third_party";
client.load(
  [protoRoot, thirdPartyRoot],
  "proto/user/user_service.proto",
  "proto/journal/journal_service.proto",
  "proto/util/util_service.proto",
);

// ---------- Custom metrics ----------
const grpcCreateUserDuration = new Trend("grpc_create_user_duration", true);
const grpcCreateJournalDuration = new Trend(
  "grpc_create_journal_duration",
  true,
);
const grpcGetJournalsDuration = new Trend("grpc_get_journals_duration", true);
const grpcTriggerAnalysisDuration = new Trend(
  "grpc_trigger_analysis_duration",
  true,
);
const grpcJournalsCreated = new Counter("grpc_journals_created");

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
    grpc_req_duration: ["p(95)<500", "p(99)<1000"],
    grpc_create_user_duration: ["p(95)<600"],
    grpc_create_journal_duration: ["p(95)<800"],
    grpc_get_journals_duration: ["p(95)<400"],
  },
};

// ---------- Setup: wait for backend readiness via HTTP, then gRPC will be ready too ----------
export function setup() {
  waitForReady(BASE_URL);
}

// ---------- Lifecycle ----------
export default function () {
  // Connect at the start of each VU iteration.
  client.connect(GRPC_ADDR, { plaintext: true });

  let userId;

  // 1. Create user via gRPC
  group("gRPC CreateUser", () => {
    const start = Date.now();
    const res = client.invoke("user.UserService/CreateUser", {
      email: randomEmail(),
      password: randomPassword(),
    });
    grpcCreateUserDuration.add(Date.now() - start);

    const ok = check(res, {
      "CreateUser: status OK": (r) => r && r.status === grpc.StatusOK,
      "CreateUser: has user_id": (r) =>
        r && r.message && (r.message.user_id || r.message.userId),
    });

    if (ok && res.message) {
      userId = res.message.user_id || res.message.userId;
    }
  });

  if (!userId) {
    client.close();
    return;
  }

  sleep(0.3);

  // 2. Create journal entry
  let journalId;
  group("gRPC CreateJournal", () => {
    const start = Date.now();
    const res = client.invoke("journal.JournalService/CreateJournal", {
      user_id: userId,
      journal_text: randomJournalText(),
      user_mood: randomMood(),
    });
    grpcCreateJournalDuration.add(Date.now() - start);

    const ok = check(res, {
      "CreateJournal: status OK": (r) => r && r.status === grpc.StatusOK,
      "CreateJournal: has journal_id": (r) =>
        r && r.message && (r.message.journal_id || r.message.journalId),
    });

    if (ok && res.message) {
      grpcJournalsCreated.add(1);
      journalId = res.message.journal_id || res.message.journalId;
    }
  });

  sleep(0.3);

  // 3. Get journals for user
  group("gRPC GetJournals", () => {
    const start = Date.now();
    const res = client.invoke("journal.JournalService/GetJournals", {
      user_id: userId,
      limit: 10,
      offset: 0,
    });
    grpcGetJournalsDuration.add(Date.now() - start);

    check(res, {
      "GetJournals: status OK": (r) => r && r.status === grpc.StatusOK,
      "GetJournals: has journals": (r) =>
        r && r.message && Array.isArray(r.message.journals),
    });
  });

  sleep(0.3);

  // 4. TriggerJournalAnalysis (gRPC-only endpoint, no HTTP mapping)
  if (journalId) {
    group("gRPC TriggerJournalAnalysis", () => {
      const start = Date.now();
      const res = client.invoke(
        "journal.JournalService/TriggerJournalAnalysis",
        {
          journal_id: journalId,
        },
      );
      grpcTriggerAnalysisDuration.add(Date.now() - start);

      check(res, {
        "TriggerJournalAnalysis: status OK": (r) =>
          r && r.status === grpc.StatusOK,
        "TriggerJournalAnalysis: success true": (r) =>
          r && r.message && r.message.success === true,
      });
    });
  }

  sleep(0.3);

  // 5. Utility endpoint
  group("gRPC GenerateRandomString", () => {
    const res = client.invoke("util.UtilService/GenerateRandomString", {});

    check(res, {
      "GenerateRandomString: status OK": (r) => r && r.status === grpc.StatusOK,
      "GenerateRandomString: has value": (r) =>
        r &&
        r.message &&
        typeof (r.message.random_string || r.message.randomString) === "string",
    });
  });

  client.close();
}
