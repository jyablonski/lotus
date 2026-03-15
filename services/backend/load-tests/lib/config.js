// Shared k6 configuration for Lotus backend load tests.
//
// Override defaults with environment variables:
//   k6 run -e BASE_URL=http://staging:8080 scripts/http-gateway-load.js

export const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
export const GRPC_ADDR = __ENV.GRPC_ADDR || "localhost:50051";
export const BACKEND_API_KEY = __ENV.BACKEND_API_KEY || "lotus-backend-dev-key";

// Default thresholds applied to every scenario unless overridden.
export const defaultThresholds = {
  http_req_failed: ["rate<0.01"], // <1% errors
  http_req_duration: ["p(95)<500", "p(99)<1000"], // 95th < 500ms, 99th < 1s
};

// Preset executor configurations for common patterns.
export const presets = {
  // Quick validation that endpoints work under minimal load.
  smoke: {
    executor: "constant-arrival-rate",
    rate: 1,
    timeUnit: "1s",
    duration: "30s",
    preAllocatedVUs: 2,
    maxVUs: 5,
  },

  // Moderate sustained load for baseline measurements.
  average: {
    executor: "constant-arrival-rate",
    rate: 10,
    timeUnit: "1s",
    duration: "2m",
    preAllocatedVUs: 20,
    maxVUs: 50,
  },

  // Ramp up to find the breaking point.
  stress: {
    executor: "ramping-arrival-rate",
    startRate: 1,
    timeUnit: "1s",
    preAllocatedVUs: 50,
    maxVUs: 200,
    stages: [
      { target: 10, duration: "30s" },
      { target: 50, duration: "1m" },
      { target: 100, duration: "1m" },
      { target: 0, duration: "30s" },
    ],
  },
};
