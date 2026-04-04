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

export interface KeywordSearchResult {
  journal: JournalEntry;
  rank: number;
}

export interface KeywordSearchResponse {
  results: KeywordSearchResult[];
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
    revalidatePath(ROUTES.profile);

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
 * Server action to update an existing journal entry.
 */
export async function updateJournal(
  journalId: string,
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

    const response = await fetch(
      `${BACKEND_URL}/v1/journals/${encodeURIComponent(journalId)}`,
      {
        method: "PATCH",
        headers: backendHeaders(),
        body: JSON.stringify({
          user_id: session.user.id,
          journal_text: journalText,
          user_mood: String(mood),
        }),
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error updating journal:", errorText);
      return {
        success: false,
        error: `Failed to update journal: ${response.status}`,
      };
    }

    revalidatePath(ROUTES.home);
    revalidatePath(ROUTES.journal.home);
    revalidatePath(ROUTES.journal.calendar);
    revalidatePath(ROUTES.profile);
    revalidatePath(ROUTES.journal.detail(journalId));

    return { success: true, journalId };
  } catch (error) {
    console.error("Error updating journal:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to update journal",
    };
  }
}

export interface DeleteJournalResult {
  success: boolean;
  error?: string;
}

/**
 * Server action to delete a journal entry.
 */
export async function deleteJournal(
  journalId: string,
): Promise<DeleteJournalResult> {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/journals/${encodeURIComponent(journalId)}?user_id=${encodeURIComponent(session.user.id)}`,
      {
        method: "DELETE",
        headers: backendHeaders(),
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error deleting journal:", errorText);
      return {
        success: false,
        error: `Failed to delete journal: ${response.status}`,
      };
    }

    revalidatePath(ROUTES.home);
    revalidatePath(ROUTES.journal.home);
    revalidatePath(ROUTES.journal.calendar);
    revalidatePath(ROUTES.profile);
    // Do not revalidate the detail URL: the client is often still on /journal/[id]
    // when this returns; invalidating that path triggers an immediate RSC refetch
    // and GetJournal for an id that was just deleted.

    return { success: true };
  } catch (error) {
    console.error("Error deleting journal:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to delete journal",
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

/**
 * Server action for keyword-based full-text search over journals.
 * Uses PostgreSQL tsvector/tsquery via the Go backend's KeywordSearchJournals RPC.
 */
export async function keywordSearchJournals(
  query: string,
  limit: number = 20,
): Promise<KeywordSearchResponse> {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return { results: [], error: "Unauthorized" };
    }

    const response = await fetch(`${BACKEND_URL}/v1/journals/keyword-search`, {
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
      console.error("Backend keyword search error:", errorText);
      return { results: [], error: `Search failed: ${response.status}` };
    }

    const data = await response.json();

    const results: KeywordSearchResult[] = (data.results ?? []).map(
      (r: { journal: BackendJournal; rank: number }) => ({
        journal: transformBackendJournal(r.journal),
        rank: r.rank,
      }),
    );

    return { results };
  } catch (error) {
    console.error("Error in keyword search:", error);
    return {
      results: [],
      error: error instanceof Error ? error.message : "Keyword search failed",
    };
  }
}

export type RequestExportResult = { exportId: string } | { error: string };

export async function requestJournalExport(
  format: "csv" | "markdown",
): Promise<RequestExportResult> {
  const session = await auth();
  if (!session?.user?.id) {
    return { error: "Unauthorized" };
  }

  try {
    const response = await fetch(`${BACKEND_URL}/v1/journals/export`, {
      method: "POST",
      headers: { ...backendHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: session.user.id, format }),
      cache: "no-store",
    });

    if (!response.ok) {
      return { error: `Export request failed: ${response.status}` };
    }

    const data = await response.json();
    return { exportId: data.exportId };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : "Export request failed",
    };
  }
}

export type PollExportResult =
  | { status: "pending" | "processing" }
  | { status: "complete"; content: string; filename: string; mimeType: string }
  | { status: "failed" }
  | { error: string };

export async function pollJournalExport(
  exportId: string,
): Promise<PollExportResult> {
  const session = await auth();
  if (!session?.user?.id) {
    return { error: "Unauthorized" };
  }

  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/journals/export/${exportId}?user_id=${session.user.id}`,
      {
        method: "GET",
        headers: backendHeaders(),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return { error: `Poll failed: ${response.status}` };
    }

    const data = await response.json();

    if (data.status === "complete") {
      return {
        status: "complete",
        content: data.content,
        filename: data.filename,
        mimeType: data.mimeType,
      };
    }

    if (data.status === "failed") {
      return { status: "failed" };
    }

    return { status: data.status as "pending" | "processing" };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : "Poll failed",
    };
  }
}
