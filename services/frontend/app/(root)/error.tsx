"use client";

import { useEffect } from "react";
import { Card, CardContent } from "@/components/ui/Card";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div className="page-container">
      <div className="content-container">
        <Card>
          <CardContent className="p-8 text-center">
            <h2 className="heading-2 mb-4 text-red-600">
              Something went wrong
            </h2>
            <p className="text-muted-dark mb-6">
              We couldn&apos;t load your dashboard. This might be a temporary
              issue.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={reset}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Try again
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
