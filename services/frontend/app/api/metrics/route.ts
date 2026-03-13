import { metricsRegistry } from "@/lib/server/metrics";

// Always re-evaluate so Prometheus gets live values on every scrape.
export const dynamic = "force-dynamic";

export async function GET() {
  const metrics = await metricsRegistry.metrics();
  return new Response(metrics, {
    headers: { "Content-Type": metricsRegistry.contentType },
  });
}
