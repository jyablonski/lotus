"use server";

import { auth } from "@/auth";
import { revalidatePath } from "next/cache";
import { BACKEND_URL } from "@/lib/config";
import { ROUTES } from "@/lib/routes";
import { MOOD_MIN, MOOD_MAX } from "@/lib/utils/moodMapping";
import { backendHeaders } from "@/lib/server/backendHeaders";
import type { JournalEntry, BackendJournal } from "@/types/journal";
import { transformBackendJournal } from "@/types/journal";

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

export interface SemanticSearchResult {
  journal: JournalEntry;
  similarityScore: number;
}

export interface SemanticSearchResponse {
  results: SemanticSearchResult[];
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
      headers: backendHeaders(),
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
          headers: backendHeaders(),
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

/**
 * Server action for semantic search over journals.
 * Calls the Go backend's SearchJournals RPC via grpc-gateway.
 */
export async function searchJournals(
  query: string,
  limit: number = 20,
): Promise<SemanticSearchResponse> {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return { results: [], error: "Unauthorized" };
    }

    const response = await fetch(`${BACKEND_URL}/v1/journals/search`, {
      method: "POST",
      headers: backendHeaders(),
      body: JSON.stringify({
        user_id: session.user.id,
        query,
        limit,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend semantic search error:", errorText);
      return { results: [], error: `Search failed: ${response.status}` };
    }

    const data = await response.json();

    const results: SemanticSearchResult[] = (data.results ?? []).map(
      (r: { journal: BackendJournal; similarityScore: number }) => ({
        journal: transformBackendJournal(r.journal),
        similarityScore: r.similarityScore,
      }),
    );

    return { results };
  } catch (error) {
    console.error("Error in semantic search:", error);
    return {
      results: [],
      error: error instanceof Error ? error.message : "Semantic search failed",
    };
  }
}
