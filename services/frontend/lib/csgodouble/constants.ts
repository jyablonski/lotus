export const KEY_NEXT_ROLL = "csgodouble:next_roll_at";
export const KEY_HISTORY = "csgodouble:history";
export const KEY_ROLL_LOCK = "csgodouble:roll_lock";

/** How long between rolls. */
export const ROLL_INTERVAL_MS = 45_000;

/**
 * Client spends ~12s displaying the spin (10s) + win reveal (2s) before
 * showing the next countdown. Add this buffer so the countdown starts at
 * ~45s after the reveal.
 */
export const DISPLAY_BUFFER_MS = 12_000;

/** How many past results to keep in history. */
export const HISTORY_LENGTH = 10;

/** Allow a roll up to this many ms before nextRollAt (handles clock skew). */
export const GRACE_MS = 2_000;

/** Redis lock TTL — covers the full roll + write operation with margin. */
export const LOCK_TTL_MS = 5_000;
