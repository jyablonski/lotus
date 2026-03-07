/**
 * Timezone-aware date formatting utilities.
 *
 * All functions accept an IANA timezone string (e.g. "America/Los_Angeles")
 * and use Intl.DateTimeFormat for deterministic output on both server and client.
 * This avoids hydration mismatches since the timezone comes from the JWT session,
 * which is available server-side.
 */

/**
 * Format a timestamp as a full entry date.
 * Example: "Sunday, June 15, 7:30 AM"
 */
export function formatEntryDate(dateString: string, timezone: string): string {
  const date = new Date(dateString);
  const dayName = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    timeZone: timezone,
  }).format(date);
  const monthDay = new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    timeZone: timezone,
  }).format(date);
  const time = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: timezone,
  }).format(date);

  return `${dayName}, ${monthDay}, ${time}`;
}

/**
 * Format a timestamp as a short date.
 * Example: "6/15/2025"
 */
export function formatShortDate(dateString: string, timezone: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    month: "numeric",
    day: "numeric",
    year: "numeric",
    timeZone: timezone,
  }).format(date);
}

/**
 * Format a Date as month and year.
 * Example: "June 2025"
 */
export function formatMonthYear(date: Date, timezone: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    year: "numeric",
    timeZone: timezone,
  }).format(date);
}

/**
 * Format a timestamp for profile display.
 * Example: "June 15, 2025"
 */
export function formatProfileDate(
  dateString: string,
  timezone: string,
): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: timezone,
  }).format(date);
}

/**
 * Format a Date as YYYY-MM-DD in the given timezone.
 * Replaces the old `toLocalDateString` which used the runtime's local timezone.
 * Used for calendar day grouping, streak calculations, etc.
 */
export function toTimezoneDateString(date: Date, timezone: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: timezone,
  }).formatToParts(date);

  const year = parts.find((p) => p.type === "year")!.value;
  const month = parts.find((p) => p.type === "month")!.value;
  const day = parts.find((p) => p.type === "day")!.value;

  return `${year}-${month}-${day}`;
}

/**
 * Get the weekday name for a date in the given timezone.
 * Example: "Monday"
 */
export function getWeekdayName(dateString: string, timezone: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    timeZone: timezone,
  }).format(date);
}
