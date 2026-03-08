export type JournalEntry = {
  journalId: string;
  userId: string;
  journalText: string;
  userMood: number;
  createdAt: string;
  /** OpenAI-generated topic tags (async; may be empty for new entries). */
  topicNames?: string[];
};

/**
 * Raw journal shape returned by the Go backend.
 * The backend returns userMood as a string; we convert to number on the frontend.
 */
export interface BackendJournal {
  journalId: string;
  userId: string;
  journalText: string;
  userMood: string;
  createdAt: string;
  /** Backend may send snake_case (topic_names) or camelCase (topicNames) depending on gateway */
  topic_names?: string[];
  topicNames?: string[];
}

/** Transform a backend journal response into the frontend JournalEntry type. */
export function transformBackendJournal(raw: BackendJournal): JournalEntry {
  const topicNames =
    (raw.topic_names?.length ? raw.topic_names : undefined) ??
    (raw.topicNames?.length ? raw.topicNames : undefined);
  return {
    journalId: raw.journalId,
    userId: raw.userId,
    journalText: raw.journalText,
    userMood: parseInt(raw.userMood, 10),
    createdAt: raw.createdAt,
    topicNames,
  };
}
