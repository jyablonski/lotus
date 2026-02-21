"use client";

import { ErrorFallback } from "@/components/ui/ErrorFallback";

export default function CalendarError({
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
      logLabel="Calendar error"
      message="We couldn't load your calendar. This might be a temporary issue."
      backHref="/"
    />
  );
}
