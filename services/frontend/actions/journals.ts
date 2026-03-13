"use server";

import { auth } from "@/auth";
import { context, propagation } from "@opentelemetry/api";
import { revalidatePath } from "next/cache";
import { BACKEND_URL } from "@/lib/config";
import { ROUTES } from "@/lib/routes";
import { MOOD_MIN, MOOD_MAX } from "@/lib/utils/moodMapping";

/** Inject W3C traceparent/tracestate from the active OTel span into a headers object. */
function withTraceHeaders(
  base: Record<string, string>,
): Record<string, string> {
  const headers = { ...base };
  propagation.inject(context.active(), headers);
  return headers;
}

export interface CreateJournalInput {
  journalText: string;
  moodScore: number;
}

export interface CreateJournalResult {
  success: boolean;
  journalId?: string;
  totalCount?: number;
  error?: string;
}

/**
 * Server action to create a new journal entry
 * This bypasses the API route and calls the Go backend directly
 */
export async function createJournal(
  input: CreateJournalInput,
): Promise<CreateJournalResult> {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const { journalText, moodScore } = input;

    if (!journalText || journalText.trim().length === 0) {
      return { success: false, error: "Journal text is required" };
    }

    const mood = Number(moodScore);
    if (!Number.isInteger(mood) || mood < MOOD_MIN || mood > MOOD_MAX) {
      return {
        success: false,
        error: `Mood must be between ${MOOD_MIN} and ${MOOD_MAX}`,
      };
    }

    const response = await fetch(`${BACKEND_URL}/v1/journals`, {
      method: "POST",
      headers: withTraceHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        user_id: session.user.id,
        journal_text: journalText,
        user_mood: String(mood),
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error creating journal:", errorText);
      return {
        success: false,
        error: `Failed to create journal: ${response.status}`,
      };
    }

    const data = await response.json();

    // Fetch the updated total count so the client can detect first-entry
    let totalCount: number | undefined;
    try {
      const countResp = await fetch(
        `${BACKEND_URL}/v1/journals?user_id=${session.user.id}&limit=1&offset=0`,
        {
          method: "GET",
          headers: withTraceHeaders({ "Content-Type": "application/json" }),
        },
      );
      if (countResp.ok) {
        const countData = await countResp.json();
        totalCount = parseInt(countData.totalCount, 10) || undefined;
      }
    } catch {
      // Non-critical — analytics only; swallow silently
    }

    // Revalidate cached data on pages that display journals
    revalidatePath(ROUTES.home);
    revalidatePath(ROUTES.journal.home);
    revalidatePath(ROUTES.journal.calendar);

    return {
      success: true,
      journalId: data.journalId,
      totalCount,
    };
  } catch (error) {
    console.error("Error creating journal:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to create journal",
    };
  }
}
