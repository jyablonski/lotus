import "server-only";

import { Registry, collectDefaultMetrics } from "prom-client";

// Singleton registry attached to globalThis so it survives Next.js hot reloads.
// Mirrors the same pattern used for the Redis client.
const globalForMetrics = globalThis as unknown as {
  __promRegistry?: Registry;
};

if (!globalForMetrics.__promRegistry) {
  const registry = new Registry();
  collectDefaultMetrics({
    register: registry,
    labels: { service: "lotus-frontend" },
  });
  globalForMetrics.__promRegistry = registry;
}

export const metricsRegistry = globalForMetrics.__promRegistry;
