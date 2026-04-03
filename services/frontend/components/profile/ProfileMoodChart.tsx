"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { JournalEntry } from "@/types/journal";
import { buildMoodDailySeries } from "@/lib/utils/moodSeries";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";

type Range = 30 | 60 | 90;

interface ProfileMoodChartProps {
  journals: JournalEntry[];
  timezone: string;
}

export function ProfileMoodChart({
  journals,
  timezone,
}: ProfileMoodChartProps) {
  const [range, setRange] = useState<Range>(30);

  const data = useMemo(
    () => buildMoodDailySeries(journals, timezone, range),
    [journals, timezone, range],
  );

  if (journals.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h2 className="text-xl font-semibold text-dark-50">Mood over time</h2>
          <div className="flex rounded-lg border border-dark-600 p-0.5 bg-dark-800/50">
            {([30, 60, 90] as const).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setRange(d)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  range === d
                    ? "bg-lotus-600/30 text-lotus-200"
                    : "text-dark-400 hover:text-dark-200"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
        <p className="text-sm text-dark-400 font-normal mt-1">
          Daily average mood when you wrote at least one entry (1–10 scale).
        </p>
      </CardHeader>
      <CardContent className="pt-0">
        {data.length === 0 ? (
          <p className="text-sm text-dark-400 py-8 text-center">
            No entries in this period — keep journaling to see your trend.
          </p>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data}
                margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="label"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={[1, 10]}
                  ticks={[1, 3, 5, 7, 10]}
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  width={28}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "#e2e8f0" }}
                  formatter={(value) => [
                    value != null ? `${value}` : "",
                    "Avg mood",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="avgMood"
                  stroke="#a78bfa"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#a78bfa" }}
                  activeDot={{ r: 5 }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
