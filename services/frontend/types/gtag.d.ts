/**
 * Minimal type declarations for the Google gtag.js global.
 *
 * These are intentionally loose (using `...args: unknown[]`) for the
 * catch-all overload so we don't have to enumerate every possible
 * gtag call signature.
 */

interface Window {
  // gtag function injected by the gtag.js script
  gtag: (
    command: "config" | "event" | "set" | "js",
    targetOrName: string | Date,
    params?: Record<string, unknown>,
  ) => void;
  // dataLayer array used by gtag
  dataLayer: Array<unknown>;
}
