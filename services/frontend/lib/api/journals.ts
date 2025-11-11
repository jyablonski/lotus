import { JournalEntry } from "@/types/journal";

export type { JournalEntry };

export interface CreateJournalParams {
  entry: string;
  mood: number; // ← Changed from string to number
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface JournalsResponse {
  journals: JournalEntry[];
  totalCount: number;
  hasMore: boolean;
}

export async function fetchJournalsByUserId({
  limit = 10,
  offset = 0,
}: PaginationParams): Promise<JournalsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const response = await fetch(`/api/journals?${params}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} ${errorText}`);
  }

  const data = await response.json();

  // Debug logging
  console.log("Raw API response:", data);
  console.log("First journal userMood:", data.journals[0]?.userMood);
  console.log("Type of userMood:", typeof data.journals[0]?.userMood);

  return {
    journals: data.journals,
    totalCount: parseInt(data.totalCount),
    hasMore: data.hasMore,
  };
}

export async function createJournalEntry({ entry, mood }: CreateJournalParams) {
  const response = await fetch("/api/journals", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      journal_text: entry,
      mood_score: mood, // ← Changed from user_mood to mood_score to match DB column
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function fetchMoreJournals({
  currentJournals,
  limit = 10,
}: {
  currentJournals: JournalEntry[];
  limit?: number;
}): Promise<JournalsResponse> {
  return fetchJournalsByUserId({
    limit,
    offset: currentJournals.length,
  });
}

export async function fetchAllJournalsByUserId(): Promise<JournalEntry[]> {
  const response = await fetchJournalsByUserId({
    limit: 1000,
  });
  return response.journals;
}
