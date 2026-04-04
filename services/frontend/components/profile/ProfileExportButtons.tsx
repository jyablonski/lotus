"use client";

import { useEffect, useRef, useState } from "react";
import { FileDown, FileText } from "lucide-react";
import { requestJournalExport, pollJournalExport } from "@/actions/journals";

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 60000;

function triggerDownload(
  content: string,
  filename: string,
  mimeType: string,
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ProfileExportButtons() {
  const [activeFormat, setActiveFormat] = useState<"csv" | "md" | null>(null);
  const [lastDownload, setLastDownload] = useState<{
    filename: string;
    at: Date;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const busy = activeFormat !== null;

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  useEffect(() => stopPolling, []);

  const startPolling = (exportId: string) => {
    intervalRef.current = setInterval(async () => {
      const result = await pollJournalExport(exportId);

      if ("error" in result) {
        stopPolling();
        setActiveFormat(null);
        setError(result.error);
        return;
      }

      if (result.status === "complete") {
        stopPolling();
        setActiveFormat(null);
        triggerDownload(result.content, result.filename, result.mimeType);
        setLastDownload({ filename: result.filename, at: new Date() });
        return;
      }

      if (result.status === "failed") {
        stopPolling();
        setActiveFormat(null);
        setError("Export failed. Please try again.");
      }
    }, POLL_INTERVAL_MS);

    timeoutRef.current = setTimeout(() => {
      stopPolling();
      setActiveFormat(null);
      setError("Export timed out. Please try again.");
    }, POLL_TIMEOUT_MS);
  };

  const run = async (kind: "csv" | "md") => {
    setError(null);
    setActiveFormat(kind);

    const result = await requestJournalExport(
      kind === "csv" ? "csv" : "markdown",
    );

    if ("error" in result) {
      setActiveFormat(null);
      setError(result.error);
      return;
    }

    startPolling(result.exportId);
  };

  return (
    <div className="space-y-2">
      {lastDownload ? (
        <p className="text-sm text-dark-400 mb-2">
          <span className="text-green-400 font-medium">
            {lastDownload.filename}
          </span>{" "}
          downloaded at{" "}
          {lastDownload.at.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
          .
        </p>
      ) : (
        <p className="text-sm text-dark-400 mb-2">
          Download everything you&apos;ve written in Lotus.
        </p>
      )}
      {error && (
        <p className="text-sm text-red-400 mb-2" role="alert">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => run("csv")}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-dark-600 text-dark-200 hover:bg-dark-700/50 disabled:opacity-50"
        >
          <FileDown size={18} className="text-lotus-400" />
          {activeFormat === "csv" ? "Preparing…" : "Export CSV"}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => run("md")}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-dark-600 text-dark-200 hover:bg-dark-700/50 disabled:opacity-50"
        >
          <FileText size={18} className="text-lotus-400" />
          {activeFormat === "md" ? "Preparing…" : "Export Markdown"}
        </button>
      </div>
    </div>
  );
}
