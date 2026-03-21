import { context, propagation } from "@opentelemetry/api";
import { BACKEND_API_KEY } from "@/lib/config";

/**
 * Build headers for any server-side fetch to the Go backend.
 * Always includes Authorization and optionally injects W3C traceparent
 * when there is an active OpenTelemetry span context.
 */
export function backendHeaders(
  base: Record<string, string> = {},
): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...base,
    Authorization: `Bearer ${BACKEND_API_KEY}`,
  };
  propagation.inject(context.active(), headers);
  return headers;
}
