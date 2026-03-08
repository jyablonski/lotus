/**
 * GA4 Analytics utility module.
 *
 * All custom event tracking should go through `trackEvent()` rather than
 * calling `gtag()` directly. This keeps a single choke-point so we can
 * gate on the presence of gtag (it won't be loaded when GA4_MEASUREMENT_ID
 * is unset) and makes it easy to add debug logging in one place.
 */

// Re-export a typed helper so callers don't need to check for window/gtag.
type GtagEventParams = Record<string, string | number | boolean | undefined>;

/**
 * Fire a GA4 custom event.
 *
 * Safe to call even when gtag.js has not been loaded (e.g. when the
 * GA4_MEASUREMENT_ID env var is blank). The call is simply a no-op in
 * that case.
 */
export function trackEvent(name: string, params: GtagEventParams = {}): void {
  if (typeof window !== "undefined" && typeof window.gtag === "function") {
    window.gtag("event", name, params);
  }
}

/**
 * Return the GA4 "time of day" bucket for the current local hour.
 *
 *   morning   = 05:00 - 11:59
 *   afternoon = 12:00 - 16:59
 *   evening   = 17:00 - 20:59
 *   night     = 21:00 - 04:59
 */
export function getTimeOfDay(): "morning" | "afternoon" | "evening" | "night" {
  const hour = new Date().getHours();
  if (hour >= 5 && hour <= 11) return "morning";
  if (hour >= 12 && hour <= 16) return "afternoon";
  if (hour >= 17 && hour <= 20) return "evening";
  return "night";
}

/**
 * Count words in a string (split on whitespace, ignore empty tokens).
 */
export function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}
