// next/cache must be mocked before importing the module under test so revalidatePath is the jest mock.
jest.mock("next/cache", () => ({
  revalidatePath: jest.fn(),
}));

jest.mock("@/auth", () => ({
  auth: jest.fn(),
}));

import { createJournal } from "@/actions/journals";
import { auth } from "@/auth";
import { revalidatePath } from "next/cache";

const mockAuth = auth as jest.MockedFunction<typeof auth>;
const mockRevalidatePath = revalidatePath as jest.MockedFunction<
  typeof revalidatePath
>;
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("createJournal", () => {
  test("returns Unauthorized when session has no user id", async () => {
    mockAuth.mockResolvedValueOnce(null as never);

    const result = await createJournal({
      journalText: "Hello",
      moodScore: 7,
    });

    expect(result.success).toBe(false);
    expect(result.error).toBe("Unauthorized");
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test("returns error when journalText is empty", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);

    const result = await createJournal({ journalText: "", moodScore: 7 });

    expect(result.success).toBe(false);
    expect(result.error).toBe("Journal text is required");
  });

  test("returns error when journalText is whitespace only", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);

    const result = await createJournal({ journalText: "   ", moodScore: 7 });

    expect(result.success).toBe(false);
    expect(result.error).toBe("Journal text is required");
  });

  test("sends correct payload to backend and returns journalId on success", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journalId: "new-journal-123" }),
    });

    const result = await createJournal({
      journalText: "My journal entry",
      moodScore: 7,
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/v1/journals"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          user_id: "u1",
          journal_text: "My journal entry",
          user_mood: "7",
        }),
      }),
    );

    expect(result.success).toBe(true);
    expect(result.journalId).toBe("new-journal-123");
  });

  test("revalidates paths on success", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journalId: "j1" }),
    });

    await createJournal({ journalText: "Entry", moodScore: 5 });

    expect(mockRevalidatePath).toHaveBeenCalledWith("/");
    expect(mockRevalidatePath).toHaveBeenCalledWith("/journal/home");
    expect(mockRevalidatePath).toHaveBeenCalledWith("/journal/calendar");
  });

  test("returns error on backend non-ok response", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => "Internal server error",
    });

    const result = await createJournal({
      journalText: "Entry",
      moodScore: 5,
    });

    expect(result.success).toBe(false);
    expect(result.error).toBe("Failed to create journal: 500");
    expect(mockRevalidatePath).not.toHaveBeenCalled();
  });

  test("returns error on network failure", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);
    mockFetch.mockRejectedValueOnce(new Error("Connection refused"));

    const result = await createJournal({
      journalText: "Entry",
      moodScore: 5,
    });

    expect(result.success).toBe(false);
    expect(result.error).toBe("Connection refused");
  });

  test("sends moodScore as string in payload", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "u1" },
      expires: "",
    } as never);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journalId: "j1" }),
    });

    await createJournal({ journalText: "Entry", moodScore: 3 });

    const body = JSON.parse(
      (mockFetch.mock.calls[0][1] as RequestInit).body as string,
    );
    expect(body.user_mood).toBe("3");
  });
});
