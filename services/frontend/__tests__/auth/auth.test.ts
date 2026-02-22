/**
 * Tests for auth.ts
 *
 * Tests the exported authConfig callbacks (signIn, jwt, session) and the
 * underlying helper functions (fetchBackendUser, createUserInBackend) by
 * mocking global fetch.
 *
 * We import authConfig directly and test the callbacks in isolation.
 * NextAuth and its providers are mocked to prevent actual initialization.
 */

jest.mock("next-auth", () => {
  // Return a function that simply returns mock exports
  const mockFn = jest.fn((config) => ({
    handlers: {},
    auth: jest.fn(),
    signIn: jest.fn(),
    signOut: jest.fn(),
  }));
  return { __esModule: true, default: mockFn };
});

jest.mock("next-auth/providers/github", () => ({
  __esModule: true,
  default: jest.fn().mockReturnValue({ id: "github", name: "GitHub" }),
}));

// Now we can import authConfig -- NextAuth() is mocked so it won't
// try to initialize the full auth system
import { authConfig } from "@/auth";

const mockFetch = jest.fn();
global.fetch = mockFetch;

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
  jest.spyOn(console, "log").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

const callbacks = authConfig.callbacks!;

// ---------------------------------------------------------------------------
// signIn callback
// ---------------------------------------------------------------------------
describe("signIn callback", () => {
  const signIn = callbacks.signIn!;

  test("rejects sign-in when user has no email", async () => {
    const result = await signIn({
      user: { email: null },
      account: { provider: "github" },
    } as never);

    expect(result).toBe(false);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test("allows sign-in for existing backend user", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "backend-123",
        createdAt: "2025-01-01T00:00:00Z",
      }),
    });

    const user = { email: "test@example.com" } as Record<string, unknown>;
    const result = await signIn({
      user,
      account: { provider: "github" },
    } as never);

    expect(result).toBe(true);
    expect(user.backendId).toBe("backend-123");
    expect(user.createdAt).toBe("2025-01-01T00:00:00Z");
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  test("creates new user when not found in backend", async () => {
    // fetchBackendUser returns 404
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    // createUserInBackend succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "new-user-456" }),
    });
    // fetchBackendUser after creation succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "new-user-456",
        createdAt: "2025-02-01T00:00:00Z",
      }),
    });

    const user = { email: "new@example.com" } as Record<string, unknown>;
    const result = await signIn({
      user,
      account: { provider: "github" },
    } as never);

    expect(result).toBe(true);
    expect(user.backendId).toBe("new-user-456");
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  test("blocks sign-in when user creation fails", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => "Internal error",
    });

    const result = await signIn({
      user: { email: "fail@example.com" },
      account: { provider: "github" },
    } as never);

    expect(result).toBe(false);
  });

  test("blocks sign-in when fetch after creation fails", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "new-user-789" }),
    });
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    const result = await signIn({
      user: { email: "fail2@example.com" },
      account: { provider: "github" },
    } as never);

    expect(result).toBe(false);
  });

  test("handles user_id (snake_case) field format from backend", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        user_id: "snake-case-id",
        created_at: "2025-03-01T00:00:00Z",
      }),
    });

    const user = { email: "test@example.com" } as Record<string, unknown>;
    await signIn({ user, account: { provider: "github" } } as never);

    expect(user.backendId).toBe("snake-case-id");
    expect(user.createdAt).toBe("2025-03-01T00:00:00Z");
  });

  test("handles network error during fetchBackendUser", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network timeout"));

    const result = await signIn({
      user: { email: "timeout@example.com" },
      account: { provider: "github" },
    } as never);

    // fetchBackendUser catches error -> null -> tries create -> also fails (no mock)
    expect(result).toBe(false);
  });

  test("sends oauth_provider to createUserInBackend", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "u1" }),
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "u1", createdAt: "2025-01-01" }),
    });

    const user = { email: "new@example.com" } as Record<string, unknown>;
    await signIn({ user, account: { provider: "github" } } as never);

    // Second fetch call is the POST to create the user
    const createCall = mockFetch.mock.calls[1];
    const body = JSON.parse(createCall[1].body);
    expect(body.oauth_provider).toBe("github");
    expect(body.email).toBe("new@example.com");
  });
});

// ---------------------------------------------------------------------------
// jwt callback
// ---------------------------------------------------------------------------
describe("jwt callback", () => {
  const jwt = callbacks.jwt!;

  test("copies backendId and createdAt from user to token", async () => {
    const result = await jwt({
      token: {},
      user: { backendId: "b-123", createdAt: "2025-01-01T00:00:00Z" },
    } as never);

    expect(result.backendId).toBe("b-123");
    expect(result.createdAt).toBe("2025-01-01T00:00:00Z");
  });

  test("preserves existing token when no user (subsequent requests)", async () => {
    const result = await jwt({
      token: { backendId: "existing-id", createdAt: "2025-01-01" },
      user: undefined,
    } as never);

    expect(result.backendId).toBe("existing-id");
    expect(result.createdAt).toBe("2025-01-01");
  });

  test("does not overwrite token when user has no backendId", async () => {
    const result = await jwt({
      token: { backendId: "original" },
      user: {},
    } as never);

    expect(result.backendId).toBe("original");
  });
});

// ---------------------------------------------------------------------------
// session callback
// ---------------------------------------------------------------------------
describe("session callback", () => {
  const session = callbacks.session!;

  test("sets session.user.id from token.backendId", async () => {
    const result = await session({
      session: { user: { id: "" } },
      token: { backendId: "b-123", createdAt: "2025-01-01" },
      user: undefined,
    } as never);

    expect(
      (result as never as Record<string, Record<string, string>>).user.id,
    ).toBe("b-123");
    expect(
      (result as never as Record<string, Record<string, string>>).user
        .createdAt,
    ).toBe("2025-01-01");
  });

  test("falls back to user.createdAt when token has no createdAt", async () => {
    const result = await session({
      session: { user: { id: "" } },
      token: { backendId: "b-123" },
      user: { createdAt: "2025-02-01" },
    } as never);

    expect(
      (result as never as Record<string, Record<string, string>>).user
        .createdAt,
    ).toBe("2025-02-01");
  });
});
