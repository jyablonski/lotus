"use client";

import { ErrorFallback } from "@/components/ui/ErrorFallback";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorFallback
      error={error}
      reset={reset}
      logLabel="Dashboard error"
      message="We couldn't load your dashboard. This might be a temporary issue."
    />
  );
}
