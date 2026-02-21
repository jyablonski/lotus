"use client";

import { ErrorFallback } from "@/components/ui/ErrorFallback";

export default function JournalHomeError({
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
      logLabel="Journal home error"
      message="We couldn't load your journal entries. This might be a temporary issue."
      backHref="/"
    />
  );
}
