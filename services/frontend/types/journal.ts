export type JournalEntry = {
  journalId: string;
  userId: string;
  journalText: string;
  userMood: number;
  createdAt: string;
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
}

/** Transform a backend journal response into the frontend JournalEntry type. */
export function transformBackendJournal(raw: BackendJournal): JournalEntry {
  return {
    ...raw,
    userMood: parseInt(raw.userMood, 10),
  };
}
