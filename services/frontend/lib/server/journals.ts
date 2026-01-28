import "server-only";

import { JournalEntry } from "@/types/journal";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";

export interface JournalsResponse {
  journals: JournalEntry[];
  totalCount: number;
  hasMore: boolean;
}

interface BackendJournal {
  journalId: string;
  userId: string;
  journalText: string;
  userMood: string;
  createdAt: string;
}

/**
 * Fetch journals for a user from the backend (server-side only)
 * This calls the Go backend directly, bypassing the API route
 */
export async function fetchJournalsForUser(
  userId: string,
  options?: { limit?: number; offset?: number },
): Promise<JournalsResponse> {
  const { limit = 10, offset = 0 } = options ?? {};

  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/journals?user_id=${userId}&limit=${limit}&offset=${offset}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        // Cache for 30 seconds
        next: { revalidate: 30 },
      },
    );

    if (!response.ok) {
      console.error(`Backend journals error: ${response.status}`);
      return { journals: [], totalCount: 0, hasMore: false };
    }

    const data = await response.json();

    // Transform userMood from string to number
    const journals: JournalEntry[] =
      data.journals?.map((journal: BackendJournal) => ({
        ...journal,
        userMood: parseInt(journal.userMood, 10),
      })) || [];

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
 * Fetch recent journals for dashboard display
 */
export async function fetchRecentJournals(
  userId: string,
  count: number = 5,
): Promise<JournalEntry[]> {
  const response = await fetchJournalsForUser(userId, { limit: count });
  return response.journals;
}

/**
 * Fetch all journals for a user (for filtering/calendar views)
 * Uses a larger limit and no caching since we need fresh data
 */
export async function fetchAllJournalsForUser(
  userId: string,
): Promise<JournalsResponse> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/journals?user_id=${userId}&limit=1000&offset=0`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        // Shorter cache for complete data sets
        next: { revalidate: 30 },
      },
    );

    if (!response.ok) {
      console.error(`Backend journals error: ${response.status}`);
      return { journals: [], totalCount: 0, hasMore: false };
    }

    const data = await response.json();

    // Transform userMood from string to number
    const journals: JournalEntry[] =
      data.journals?.map((journal: BackendJournal) => ({
        ...journal,
        userMood: parseInt(journal.userMood, 10),
      })) || [];

    return {
      journals,
      totalCount: parseInt(data.totalCount, 10) || 0,
      hasMore: data.hasMore || false,
    };
  } catch (error) {
    console.error("Error fetching all journals:", error);
    return { journals: [], totalCount: 0, hasMore: false };
  }
}
