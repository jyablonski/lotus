import { randomInt } from "node:crypto";
import { NextResponse } from "next/server";
import { redis } from "@/lib/server/redis";

const KEY_NEXT_ROLL = "csgodouble:next_roll_at";
const KEY_HISTORY = "csgodouble:history";
const ROLL_INTERVAL_MS = 45_000;
// Client spends ~12s displaying the spin (10s) + win reveal (2s) before showing the
// next countdown. Add this buffer so the countdown starts at ~45s after the reveal.
const DISPLAY_BUFFER_MS = 12_000;
const HISTORY_LENGTH = 10;
const GRACE_MS = 2000; // allow roll up to 2s before nextRollAt (clock skew)

/** Uniform random 0..14 (crypto RNG; each number has 1/15 chance). */
function roll(): number {
  return randomInt(0, 15);
}

export async function POST() {
  try {
    const now = Date.now();
    const nextRollAtStr = await redis.get(KEY_NEXT_ROLL);
    const nextRollAt = nextRollAtStr ? parseInt(nextRollAtStr, 10) : 0;

    if (nextRollAt > now + GRACE_MS) {
      return NextResponse.json(
        { error: "Too early to roll", nextRollAt },
        { status: 429 },
      );
    }

    const result = roll();
    const historyStr = await redis.get(KEY_HISTORY);
    const history: number[] = historyStr ? JSON.parse(historyStr) : [];
    const newHistory = [result, ...history].slice(0, HISTORY_LENGTH);
    const newNextRollAt = now + ROLL_INTERVAL_MS + DISPLAY_BUFFER_MS;

    await redis
      .multi()
      .set(KEY_NEXT_ROLL, String(newNextRollAt))
      .set(KEY_HISTORY, JSON.stringify(newHistory))
      .exec();

    return NextResponse.json({
      result,
      nextRollAt: newNextRollAt,
      history: newHistory,
    });
  } catch (error) {
    console.error("[csgodouble/roll]", error);
    return NextResponse.json({ error: "Failed to roll" }, { status: 500 });
  }
}
