"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { trackEvent } from "@/lib/analytics";

interface ErrorFallbackProps {
  error: Error & { digest?: string };
  reset: () => void;
  /** Label for the console.error log */
  logLabel: string;
  /** User-facing description of what failed to load */
  message: string;
  /** Optional link to navigate away. Omit to hide the secondary button. */
  backHref?: string;
  /** Label for the back link button */
  backLabel?: string;
}

export function ErrorFallback({
  error,
  reset,
  logLabel,
  message,
  backHref,
  backLabel = "Go to Dashboard",
}: ErrorFallbackProps) {
  const pathname = usePathname();

  useEffect(() => {
    console.error(`${logLabel}:`, error);

    // §3e: error_encountered — fire when any error boundary catches an error
    trackEvent("error_encountered", {
      error_type: "load_failed",
      page: pathname ?? "unknown",
    });
  }, [error, logLabel, pathname]);

  return (
    <div className="page-container">
      <div className="content-container">
        <Card>
          <CardContent className="p-8 text-center">
            <h2 className="heading-2 mb-4 text-rose-400">
              Something went wrong
            </h2>
            <p className="text-muted-dark mb-6">{message}</p>
            <div className="flex gap-4 justify-center">
              <button onClick={reset} className="btn-primary">
                Try again
              </button>
              {backHref && (
                <Link href={backHref} className="btn-outline">
                  {backLabel}
                </Link>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
