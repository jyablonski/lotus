"use client";

import { useState, useTransition } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { submitErrorDemo } from "@/actions/errorDemo";

export default function ErrorDemoPage() {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const result = await submitErrorDemo(value);
      if (!result.success) {
        setError(result.error ?? "Something went wrong. Please try again.");
      }
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="heading-1">Error Handling Demo</h1>
      </div>

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="alert-error">
                <p className="text-sm">{error}</p>
              </div>
            )}

            <div>
              <label htmlFor="demo-input" className="label">
                Value (saves to nothing)
              </label>
              <input
                id="demo-input"
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Type anything..."
                className="input-primary w-full"
                disabled={isPending}
              />
            </div>

            <button
              type="submit"
              disabled={isPending}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
            >
              {isPending ? (
                <>
                  <span
                    className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
                    aria-hidden
                  />
                  Saving...
                </>
              ) : (
                "Save"
              )}
            </button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
