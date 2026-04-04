import "server-only";

import {
  JournalEntry,
  BackendJournal,
  transformBackendJournal,
} from "@/types/journal";
import { BACKEND_URL } from "@/lib/config";
import { backendHeaders } from "@/lib/server/backendHeaders";

export interface JournalsResponse {
  journals: JournalEntry[];
  totalCount: number;
  hasMore: boolean;
}

/**
 * Fetch journals for a user from the backend (server-side only).
 * Calls the Go backend directly, bypassing any API route.
 */
export async function fetchJournalsForUser(
  userId: string,
  options?: { limit?: number; offset?: number; cache?: RequestCache },
): Promise<JournalsResponse> {
  const { limit = 10, offset = 0, cache } = options ?? {};

  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/journals?user_id=${userId}&limit=${limit}&offset=${offset}`,
      {
        method: "GET",
        headers: backendHeaders(),
        ...(cache === "no-store"
          ? { cache: "no-store" as RequestCache }
          : { next: { revalidate: 30 } }),
      },
    );

    if (!response.ok) {
      console.error(`Backend journals error: ${response.status}`);
      return { journals: [], totalCount: 0, hasMore: false };
    }

    const data = await response.json();

    const journals: JournalEntry[] =
      data.journals?.map((j: BackendJournal) => transformBackendJournal(j)) ||
      [];

    return {
      journals,
      totalCount: parseInt(data.totalCount, 10) || 0,
      hasMore: data.hasMore || false,
    };
  } catch (error) {
    console.error("Error fetching journals:", error);
    return { journals: [], totalCount: 0, hasMore: false };
  }
}

/**
 * Fetch recent journals for dashboard display.
 */
export async function fetchRecentJournals(
  userId: string,
  count: number = 5,
): Promise<JournalEntry[]> {
  const response = await fetchJournalsForUser(userId, { limit: count });
  return response.journals;
}

/**
 * Fetch all journals for a user (for journal home, calendar, profile views).
 * Paginates until all rows are loaded (backend caps each page at 100).
 */
export async function fetchAllJournalsForUser(
  userId: string,
): Promise<JournalsResponse> {
  const journals: JournalEntry[] = [];
  let offset = 0;
  const limit = 100;
  let totalCount = 0;
  let hasMore = true;

  while (hasMore) {
    const page = await fetchJournalsForUser(userId, {
      limit,
      offset,
      cache: "no-store",
    });
    journals.push(...page.journals);
    totalCount = page.totalCount;
    hasMore = page.hasMore;
    offset += limit;
  }

  return {
    journals,
    totalCount,
    hasMore: false,
  };
}

/**
 * Load a single journal entry (for detail page).
 */
export async function fetchJournalById(
  userId: string,
  journalId: string,
): Promise<JournalEntry | null> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/journals/${encodeURIComponent(journalId)}?user_id=${encodeURIComponent(userId)}`,
      {
        method: "GET",
        headers: backendHeaders(),
        cache: "no-store",
      },
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      console.error(`Backend journal by id error: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const raw = data.journal;
    if (!raw) {
      return null;
    }

    return transformBackendJournal(raw as BackendJournal);
  } catch (error) {
    console.error("Error fetching journal by id:", error);
    return null;
  }
}
