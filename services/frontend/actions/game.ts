"use server";

import { auth } from "@/auth";
import { context, propagation } from "@opentelemetry/api";
import { BACKEND_URL, BACKEND_API_KEY } from "@/lib/config";

function withTraceHeaders(
  base: Record<string, string>,
): Record<string, string> {
  const headers = { ...base, Authorization: `Bearer ${BACKEND_API_KEY}` };
  propagation.inject(context.active(), headers);
  return headers;
}

export interface GameBalanceResult {
  success: boolean;
  balance?: number;
  error?: string;
}

export interface BetEntry {
  zone: string;
  amount: number;
  roll_result: number;
  payout: number;
}

export interface BetRecord {
  id: number;
  zone: string;
  amount: number;
  rollResult: number;
  payout: number;
  createdAt: string;
}

export interface RecordBetsResult {
  success: boolean;
  error?: string;
}

export interface GetBetHistoryResult {
  success: boolean;
  bets?: BetRecord[];
  error?: string;
}

/** Record bets placed during a completed roll. */
export async function recordBets(bets: BetEntry[]): Promise<RecordBetsResult> {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(`${BACKEND_URL}/v1/game/bets`, {
      method: "POST",
      headers: withTraceHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ user_id: session.user.id, bets }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error recording bets:", errorText);
      return {
        success: false,
        error: `Failed to record bets: ${response.status}`,
      };
    }

    return { success: true };
  } catch (error) {
    console.error("Error recording bets:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to record bets",
    };
  }
}

/** Fetch paginated bet history for the authenticated user. */
export async function getBetHistory(
  limit = 20,
  offset = 0,
): Promise<GetBetHistoryResult> {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/game/bets?user_id=${session.user.id}&limit=${limit}&offset=${offset}`,
      {
        method: "GET",
        headers: withTraceHeaders({ "Content-Type": "application/json" }),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error fetching bet history:", errorText);
      return {
        success: false,
        error: `Failed to fetch bet history: ${response.status}`,
      };
    }

    const data: { bets?: BetRecord[] } = await response.json();
    return { success: true, bets: data.bets ?? [] };
  } catch (error) {
    console.error("Error fetching bet history:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to fetch bet history",
    };
  }
}

/** Fetch the current game balance for the authenticated user. */
export async function getGameBalance(): Promise<GameBalanceResult> {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/game/balance?user_id=${session.user.id}`,
      {
        method: "GET",
        headers: withTraceHeaders({ "Content-Type": "application/json" }),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error fetching game balance:", errorText);
      return {
        success: false,
        error: `Failed to fetch balance: ${response.status}`,
      };
    }

    const data: { balance?: number } = await response.json();
    return { success: true, balance: data.balance ?? 100 };
  } catch (error) {
    console.error("Error fetching game balance:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to fetch balance",
    };
  }
}

/** Persist the current game balance for the authenticated user. */
export async function updateGameBalance(
  balance: number,
): Promise<GameBalanceResult> {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(`${BACKEND_URL}/v1/game/balance`, {
      method: "POST",
      headers: withTraceHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ user_id: session.user.id, balance }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error updating game balance:", errorText);
      return {
        success: false,
        error: `Failed to update balance: ${response.status}`,
      };
    }

    const data: { balance?: number } = await response.json();
    return { success: true, balance: data.balance ?? balance };
  } catch (error) {
    console.error("Error updating game balance:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to update balance",
    };
  }
}
