"use client";

import { useState } from "react";
import { FileDown, FileText } from "lucide-react";
import {
  exportJournalsAsCsv,
  exportJournalsAsMarkdown,
} from "@/actions/journals";

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
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (kind: "csv" | "md") => {
    setError(null);
    setBusy(true);
    try {
      const result =
        kind === "csv"
          ? await exportJournalsAsCsv()
          : await exportJournalsAsMarkdown();
      if ("error" in result) {
        setError(result.error);
        return;
      }
      triggerDownload(result.content, result.filename, result.mimeType);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-2">
      <p className="text-sm text-dark-400 mb-2">
        Download everything you&apos;ve written in Lotus.
      </p>
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
          {busy ? "Preparing…" : "Export CSV"}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => run("md")}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-dark-600 text-dark-200 hover:bg-dark-700/50 disabled:opacity-50"
        >
          <FileText size={18} className="text-lotus-400" />
          {busy ? "Preparing…" : "Export Markdown"}
        </button>
      </div>
    </div>
  );
}
