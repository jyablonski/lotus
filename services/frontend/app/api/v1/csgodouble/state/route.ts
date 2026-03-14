import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { redis } from "@/lib/server/redis";
import {
  KEY_NEXT_ROLL,
  KEY_HISTORY,
  ROLL_INTERVAL_MS,
} from "@/lib/csgodouble/constants";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const now = Date.now();
    const [nextRollAtStr, historyStr] = await Promise.all([
      redis.get(KEY_NEXT_ROLL),
      redis.get(KEY_HISTORY),
    ]);

    let nextRollAt = nextRollAtStr ? parseInt(nextRollAtStr, 10) : null;
    let history: number[] = [];
    try {
      history = historyStr ? JSON.parse(historyStr) : [];
    } catch {
      history = [];
    }

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
