import { randomInt, randomBytes } from "node:crypto";
import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { redis } from "@/lib/server/redis";
import {
  KEY_NEXT_ROLL,
  KEY_HISTORY,
  KEY_ROLL_LOCK,
  ROLL_INTERVAL_MS,
  DISPLAY_BUFFER_MS,
  HISTORY_LENGTH,
  GRACE_MS,
  LOCK_TTL_MS,
} from "@/lib/csgodouble/constants";

/** Uniform random 0..14 (crypto RNG; each number has 1/15 chance). */
function roll(): number {
  return randomInt(0, 15);
}

/**
 * Atomically release a Redis lock only if we still own it.
 * Prevents releasing a lock acquired by a different request after TTL expiry.
 */
const UNLOCK_SCRIPT = `
  if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
  else
    return 0
  end
`;

export async function POST() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Acquire a distributed lock to serialise concurrent roll requests.
  // SET NX PX is atomic — only one request wins.
  const lockToken = randomBytes(16).toString("hex");
  const acquired = await redis.set(
    KEY_ROLL_LOCK,
    lockToken,
    "PX",
    LOCK_TTL_MS,
    "NX",
  );

  if (!acquired) {
    // Another roll is already in progress — return current state so the
    // client can sync its countdown to the upcoming nextRollAt.
    const nextRollAtStr = await redis.get(KEY_NEXT_ROLL);
    const historyStr = await redis.get(KEY_HISTORY);
    let history: number[] = [];
    try {
      history = historyStr ? JSON.parse(historyStr) : [];
    } catch {
      history = [];
    }
    return NextResponse.json(
      {
        error: "Roll already in progress",
        nextRollAt: nextRollAtStr ? parseInt(nextRollAtStr, 10) : null,
        history,
      },
      { status: 429 },
    );
  }

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
    let history: number[] = [];
    try {
      history = historyStr ? JSON.parse(historyStr) : [];
    } catch {
      history = [];
    }

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
  } finally {
    // Always release the lock, even on error, using the safe Lua script.
    await redis.eval(UNLOCK_SCRIPT, 1, KEY_ROLL_LOCK, lockToken).catch(() => {
      // Non-fatal: lock will expire via TTL if this fails.
    });
  }
}
