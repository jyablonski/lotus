import { NextResponse } from "next/server";
import { redis } from "@/lib/server/redis";

const KEY_NEXT_ROLL = "csgodouble:next_roll_at";
const KEY_HISTORY = "csgodouble:history";
const ROLL_INTERVAL_MS = 45_000;

export async function GET() {
  try {
    const now = Date.now();
    const [nextRollAtStr, historyStr] = await Promise.all([
      redis.get(KEY_NEXT_ROLL),
      redis.get(KEY_HISTORY),
    ]);

    let nextRollAt = nextRollAtStr ? parseInt(nextRollAtStr, 10) : null;
    const history: number[] = historyStr ? JSON.parse(historyStr) : [];

    if (nextRollAt == null || nextRollAt < now) {
      nextRollAt = now + ROLL_INTERVAL_MS;
      await redis.set(KEY_NEXT_ROLL, String(nextRollAt));
    }

    return NextResponse.json({ nextRollAt, history });
  } catch (error) {
    console.error("[csgodouble/state]", error);
    return NextResponse.json(
      { error: "Failed to get game state" },
      { status: 500 },
    );
  }
}
