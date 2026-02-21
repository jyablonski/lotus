"use client";

import { ErrorFallback } from "@/components/ui/ErrorFallback";

export default function ProfileError({
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
      logLabel="Profile error"
      message="We couldn't load your profile. This might be a temporary issue."
      backHref="/"
    />
  );
}
