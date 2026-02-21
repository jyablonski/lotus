import { transformBackendJournal, BackendJournal } from "@/types/journal";

describe("transformBackendJournal", () => {
  test("converts userMood from string to number", () => {
    const raw: BackendJournal = {
      journalId: "123",
      userId: "user1",
      journalText: "Hello world",
      userMood: "7",
      createdAt: "2025-06-15T12:00:00Z",
    };
    const result = transformBackendJournal(raw);
    expect(result.userMood).toBe(7);
    expect(typeof result.userMood).toBe("number");
  });

  test("preserves all other fields", () => {
    const raw: BackendJournal = {
      journalId: "456",
      userId: "user2",
      journalText: "Some text here",
      userMood: "3",
      createdAt: "2025-01-01T00:00:00Z",
    };
    const result = transformBackendJournal(raw);
    expect(result.journalId).toBe("456");
    expect(result.userId).toBe("user2");
    expect(result.journalText).toBe("Some text here");
    expect(result.createdAt).toBe("2025-01-01T00:00:00Z");
  });

  test("handles mood value at boundaries", () => {
    const raw1: BackendJournal = {
      journalId: "1",
      userId: "u",
      journalText: "t",
      userMood: "1",
      createdAt: "2025-01-01T00:00:00Z",
    };
    expect(transformBackendJournal(raw1).userMood).toBe(1);

    const raw8: BackendJournal = {
      journalId: "2",
      userId: "u",
      journalText: "t",
      userMood: "8",
      createdAt: "2025-01-01T00:00:00Z",
    };
    expect(transformBackendJournal(raw8).userMood).toBe(8);
  });

  test("handles non-numeric mood string gracefully (NaN)", () => {
    const raw: BackendJournal = {
      journalId: "1",
      userId: "u",
      journalText: "t",
      userMood: "invalid",
      createdAt: "2025-01-01T00:00:00Z",
    };
    const result = transformBackendJournal(raw);
    expect(Number.isNaN(result.userMood)).toBe(true);
  });
});
