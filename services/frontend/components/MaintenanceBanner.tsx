"use client";

import { useState } from "react";

/**
 * A dismissible maintenance banner displayed when the `frontend_maintenance`
 * feature flag is active.  Renders at the top of the page between the Navbar
 * and the main content area.
 */
export function MaintenanceBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="relative border-b border-yellow-600/30 bg-yellow-500/10 px-4 py-3 text-center text-sm text-yellow-300">
      <p>
        <span className="font-semibold">Scheduled Maintenance:</span> We are
        performing maintenance and some features may be temporarily unavailable.
      </p>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-yellow-400 transition-colors hover:bg-yellow-500/20 hover:text-yellow-200"
        aria-label="Dismiss maintenance banner"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </div>
  );
}
