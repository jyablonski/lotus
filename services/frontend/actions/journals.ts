"use server";

import { auth } from "@/auth";
import { revalidatePath } from "next/cache";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";

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

    const response = await fetch(`${BACKEND_URL}/v1/journals`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: session.user.id,
        journal_text: journalText,
        user_mood: moodScore?.toString() || undefined,
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
        { method: "GET", headers: { "Content-Type": "application/json" } },
      );
      if (countResp.ok) {
        const countData = await countResp.json();
        totalCount = parseInt(countData.totalCount, 10) || undefined;
      }
    } catch {
      // Non-critical — analytics only; swallow silently
    }

    // Revalidate cached data on pages that display journals
    revalidatePath("/");
    revalidatePath("/journal/home");
    revalidatePath("/journal/calendar");

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
