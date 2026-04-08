import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import type { CommunityMetric } from "@/types/community";

interface CommunityMetricListProps {
  title: string;
  description: string;
  metrics: CommunityMetric[];
  emptyMessage: string;
}

function formatDelta(delta: number | null): string | null {
  if (delta === null) {
    return null;
  }

  const sign = delta > 0 ? "+" : "";
  return `${sign}${Math.round(delta * 100)}% vs previous`;
}

export function CommunityMetricList({
  title,
  description,
  metrics,
  emptyMessage,
}: CommunityMetricListProps) {
  return (
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-primary-dark">{title}</h2>
          <p className="text-sm text-muted-dark">{description}</p>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {metrics.length > 0 ? (
          metrics.map((metric) => {
            const delta = formatDelta(metric.deltaVsPrevious);

            return (
              <div
                key={`${metric.name}-${metric.rank}`}
                className="rounded-xl border border-dark-600 bg-dark-800/55 px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-base font-medium text-primary-dark capitalize">
                      {metric.name}
                    </p>
                    <p className="text-xs uppercase tracking-[0.2em] text-dark-400">
                      Rank {metric.rank}
                    </p>
                  </div>
                  {delta ? (
                    <span className="rounded-full bg-lotus-500/10 px-3 py-1 text-xs font-medium text-lotus-300">
                      {delta}
                    </span>
                  ) : (
                    <span className="rounded-full bg-dark-700 px-3 py-1 text-xs font-medium text-dark-300">
                      Holding steady
                    </span>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="rounded-xl border border-dashed border-dark-600 px-4 py-6 text-sm text-muted-dark">
            {emptyMessage}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
