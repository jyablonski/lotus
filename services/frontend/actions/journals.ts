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

    // Revalidate cached data on pages that display journals
    revalidatePath("/");
    revalidatePath("/journal/home");
    revalidatePath("/journal/calendar");

    return {
      success: true,
      journalId: data.journalId,
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
