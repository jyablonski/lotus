import "server-only";

import Redis from "ioredis";

// Singleton Redis client attached to globalThis so it survives Next.js hot
// reloads and is shared across middleware / RSC / route-handler bundles.
const globalForRedis = globalThis as unknown as { __redis?: Redis };

if (!globalForRedis.__redis) {
  globalForRedis.__redis = new Redis(
    process.env.REDIS_URL ?? "redis://localhost:6379",
    { lazyConnect: false, maxRetriesPerRequest: 3 },
  );
}

export const redis = globalForRedis.__redis;
