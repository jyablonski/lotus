// Next.js instrumentation hook — runs once at server startup.
// @vercel/otel is the recommended OTel integration for Next.js: it correctly
// instruments Next.js's patched fetch (used by Server Actions and Server
// Components), route handlers, and page rendering, and propagates W3C
// traceparent headers on all outgoing requests.
//
// Configuration is driven entirely by environment variables:
//   OTEL_EXPORTER_OTLP_ENDPOINT  → set to http://jaeger:4318 in docker-compose
//
// Prometheus metrics are handled separately via lib/server/metrics.ts.
// See: https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation

import { registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({ serviceName: "lotus-frontend" });
}
