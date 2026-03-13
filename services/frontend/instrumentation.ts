// Next.js instrumentation hook — runs once at server startup.
// @vercel/otel handles inbound request tracing (route handlers, Server Actions,
// page rendering) and configures the OTLP exporter via env vars:
//   OTEL_EXPORTER_OTLP_ENDPOINT  → set to http://jaeger:4318 in docker-compose
//
// @vercel/otel's built-in fetch patch only instruments globalThis.fetch, but
// Next.js Server Actions call undici directly, bypassing that layer. Adding
// UndiciInstrumentation patches undici at the module level, which captures all
// outbound HTTP calls and injects traceparent headers so Jaeger shows the full
// trace chain:  lotus-frontend → lotus-backend → lotus-analyzer
//
// next.config.ts lists @opentelemetry/instrumentation-undici in
// serverExternalPackages so webpack doesn't bundle it.
//
// Prometheus metrics are handled separately via lib/server/metrics.ts.
// See: https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation

import { registerOTel } from "@vercel/otel";
import { UndiciInstrumentation } from "@opentelemetry/instrumentation-undici";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";

export function register() {
  registerOTel({
    serviceName: "lotus-frontend",
    instrumentations: [new UndiciInstrumentation()],
    instrumentationConfig: {
      fetch: {
        propagateContextUrls: [BACKEND_URL],
      },
    },
  });
}
