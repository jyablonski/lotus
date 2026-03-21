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

jest.mock("next-auth/providers/resend", () => ({
  __esModule: true,
  default: jest.fn().mockReturnValue({ id: "resend", name: "Resend" }),
}));

jest.mock("@/lib/server/redis", () => ({
  redis: {
    get: jest.fn().mockResolvedValue(null),
    set: jest.fn().mockResolvedValue("OK"),
    del: jest.fn().mockResolvedValue(1),
  },
}));

jest.mock("@/lib/config", () => ({
  BACKEND_URL: "http://backend:8080",
  BACKEND_API_KEY: "test-api-key",
}));

// Now we can import authConfig -- NextAuth() is mocked so it won't
// try to initialize the full auth system
import { authConfig, __clearBackendUserCacheForTests } from "@/auth";

const mockFetch = jest.fn();
global.fetch = mockFetch;

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  jest.clearAllMocks();
  mockFetch.mockReset(); // clear implementation queue so no leftover mockResolvedValueOnce from previous tests
  __clearBackendUserCacheForTests();
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
        timezone: "America/New_York",
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
    expect(user.timezone).toBe("America/New_York");
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
        timezone: "UTC",
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
        timezone: "Europe/London",
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

  test("sends Authorization Bearer header on fetchBackendUser", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "backend-123",
        createdAt: "2025-01-01T00:00:00Z",
        timezone: "UTC",
      }),
    });

    const user = { email: "auth-header@example.com" } as Record<
      string,
      unknown
    >;
    await signIn({ user, account: { provider: "github" } } as never);

    // First fetch call is fetchBackendUser
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-api-key",
        }),
      }),
    );
  });

  test("sends Authorization Bearer header on createUserInBackend", async () => {
    // fetchBackendUser returns 404
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    // createUserInBackend succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "new-u" }),
    });
    // fetchBackendUser after creation
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "new-u",
        createdAt: "2025-01-01",
        timezone: "UTC",
      }),
    });

    const user = { email: "auth-header2@example.com" } as Record<
      string,
      unknown
    >;
    await signIn({ user, account: { provider: "github" } } as never);

    // Second fetch call is the POST to create user
    const createCall = mockFetch.mock.calls[1];
    expect(createCall[1].headers).toEqual(
      expect.objectContaining({
        Authorization: "Bearer test-api-key",
      }),
    );
  });

  test("sends oauth_provider to createUserInBackend", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "u1" }),
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "u1",
        createdAt: "2025-01-01",
        timezone: "UTC",
      }),
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
    // Token already has backendId; we do not fetch (rely on JWT after login).
    const result = await jwt({
      token: {
        backendId: "existing-id",
        email: "test@example.com",
        createdAt: "2025-01-01",
      },
      user: undefined,
    } as never);

    expect(result.backendId).toBe("existing-id");
    expect(result.createdAt).toBe("2025-01-01");
    expect(mockFetch).not.toHaveBeenCalled();
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
      token: {
        backendId: "b-123",
        createdAt: "2025-01-01",
        timezone: "America/Los_Angeles",
      },
      user: undefined,
    } as never);

    expect(
      (result as never as Record<string, Record<string, string>>).user.id,
    ).toBe("b-123");
    expect(
      (result as never as Record<string, Record<string, string>>).user
        .createdAt,
    ).toBe("2025-01-01");
    expect(
      (result as never as Record<string, Record<string, string>>).user.timezone,
    ).toBe("America/Los_Angeles");
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

// ---------------------------------------------------------------------------
// signIn callback - magic link (email) provider
// ---------------------------------------------------------------------------
describe("signIn callback - magic link (email provider)", () => {
  const signIn = callbacks.signIn!;

  test("allows phase-1 email send when user has no id yet", async () => {
    // Phase-1: email is being sent, user.id is not populated
    const result = await signIn({
      user: { email: "magic@example.com" },
      account: { provider: "resend" },
    } as never);

    expect(result).toBe(true);
    // No backend calls should happen during phase-1
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test("syncs with backend on phase-2 for existing user", async () => {
    // Phase-2: user clicked the magic link, user.id is set by the adapter
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "email-user-100",
        createdAt: "2025-05-01T00:00:00Z",
        timezone: "America/Denver",
      }),
    });

    const user = { id: "email-user-100", email: "magic@example.com" } as Record<
      string,
      unknown
    >;
    const result = await signIn({
      user,
      account: { provider: "resend" },
    } as never);

    expect(result).toBe(true);
    expect(user.backendId).toBe("email-user-100");
    expect(user.createdAt).toBe("2025-05-01T00:00:00Z");
  });

  test("creates new user in backend on phase-2 with provider 'email'", async () => {
    // Phase-2: user clicked the magic link but doesn't exist in backend yet
    // fetchBackendUser returns 404
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    // createUserInBackend succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "new-email-user-200" }),
    });
    // fetchBackendUser after creation succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "new-email-user-200",
        createdAt: "2025-06-01T00:00:00Z",
        timezone: "UTC",
      }),
    });

    const user = { id: "adapter-id", email: "newmagic@example.com" } as Record<
      string,
      unknown
    >;
    const result = await signIn({
      user,
      account: { provider: "resend" },
    } as never);

    expect(result).toBe(true);
    expect(user.backendId).toBe("new-email-user-200");

    // Verify the create call used "email" as the oauth_provider
    const createCall = mockFetch.mock.calls[1];
    const body = JSON.parse(createCall[1].body);
    expect(body.oauth_provider).toBe("email");
    expect(body.email).toBe("newmagic@example.com");
  });
});

// ---------------------------------------------------------------------------
// jwt callback - magic link fallback paths
// ---------------------------------------------------------------------------
describe("jwt callback - magic link fallback paths", () => {
  const jwt = callbacks.jwt!;

  test("falls back to user.id when user.backendId is missing (adapter user)", async () => {
    // The adapter returns AdapterUser with id = backend UUID, no backendId field
    const result = await jwt({
      token: {},
      user: { id: "adapter-uuid-999", email: "adapter@example.com" },
    } as never);

    expect(result.backendId).toBe("adapter-uuid-999");
    expect(result.email).toBe("adapter@example.com");
  });

  test("looks up backend user by email when backendId is still missing", async () => {
    // Scenario: token has email but no backendId (user object had neither
    // backendId nor a useful id). JWT callback does one lookup; no refresh fetch.
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "looked-up-id",
        createdAt: "2025-07-01T00:00:00Z",
        role: "Consumer",
        timezone: "Asia/Tokyo",
      }),
    });

    const result = await jwt({
      token: { email: "lookup@example.com" },
      user: undefined,
    } as never);

    expect(result.backendId).toBe("looked-up-id");
    expect(result.createdAt).toBe("2025-07-01T00:00:00Z");
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  test("creates user in backend when email lookup returns null", async () => {
    // fetchBackendUser returns null (404)
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    // createUserInBackend succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ userId: "auto-created-id" }),
    });
    // fetchBackendUser after creation
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "auto-created-id",
        createdAt: "2025-08-01T00:00:00Z",
        role: "Consumer",
        timezone: "UTC",
      }),
    });
    // Always-refresh-role lookup
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        userId: "auto-created-id",
        createdAt: "2025-08-01T00:00:00Z",
        role: "Consumer",
        timezone: "UTC",
      }),
    });

    const result = await jwt({
      token: { email: "autocreate@example.com" },
      user: undefined,
    } as never);

    expect(result.backendId).toBe("auto-created-id");
    expect(result.createdAt).toBe("2025-08-01T00:00:00Z");
  });

  test("handles failed email lookup and failed creation gracefully", async () => {
    // fetchBackendUser returns 404
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    // createUserInBackend fails
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => "Internal error",
    });

    const result = await jwt({
      token: { email: "failall@example.com" },
      user: undefined,
    } as never);

    // backendId should remain unset — no crash
    expect(result.backendId).toBeUndefined();
  });

  test("does not fetch when backendId is already on the token", async () => {
    // We rely on JWT after login; no backend refresh when backendId is already set.
    const result = await jwt({
      token: { backendId: "already-set", email: "skip@example.com" },
      user: undefined,
    } as never);

    expect(result.backendId).toBe("already-set");
    expect(mockFetch).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// authConfig - structural assertions
// ---------------------------------------------------------------------------
describe("authConfig structure", () => {
  test("uses JWT session strategy", () => {
    expect(authConfig.session?.strategy).toBe("jwt");
  });

  test("has custom sign-in and verify-request pages", () => {
    expect(authConfig.pages?.signIn).toBe("/signin");
    expect(authConfig.pages?.verifyRequest).toBe("/verify-request");
  });

  test("has an adapter defined (magicLinkAdapter)", () => {
    expect(authConfig.adapter).toBeDefined();
  });

  test("configures two providers", () => {
    expect(authConfig.providers).toHaveLength(2);
  });
});
