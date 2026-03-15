/**
 * Tests for actions/user.ts (updateTimezone server action)
 */

jest.mock("next/cache", () => ({}));
jest.mock("@/auth", () => ({
  auth: jest.fn(),
}));

import { updateTimezone } from "@/actions/user";
import { auth } from "@/auth";

const mockAuth = auth as jest.MockedFunction<typeof auth>;
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("updateTimezone", () => {
  it("returns Unauthorized when session has no user id", async () => {
    mockAuth.mockResolvedValueOnce(null as never);

    const result = await updateTimezone("America/New_York");

    expect(result.success).toBe(false);
    expect(result.error).toBe("Unauthorized");
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("returns Unauthorized when session user has no id", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { email: "a@b.com" },
      expires: "",
    } as never);

    const result = await updateTimezone("America/New_York");

    expect(result.success).toBe(false);
    expect(result.error).toBe("Unauthorized");
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("calls PATCH /v1/users/{userId}/timezone and returns success", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "user-123" },
      expires: "",
    } as never);
    mockFetch.mockResolvedValueOnce({ ok: true });

    const result = await updateTimezone("America/New_York");

    expect(result.success).toBe(true);
    expect(result.timezone).toBe("America/New_York");
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/v1/users/user-123/timezone"),
      expect.objectContaining({
        method: "PATCH",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
        body: JSON.stringify({ timezone: "America/New_York" }),
      }),
    );
  });

  it("returns error when backend returns non-ok", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "user-123" },
      expires: "",
    } as never);
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: () => Promise.resolve("Internal Server Error"),
    });

    const result = await updateTimezone("UTC");

    expect(result.success).toBe(false);
    expect(result.error).toContain("500");
  });

  it("returns error message on network failure", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "user-123" },
      expires: "",
    } as never);
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const result = await updateTimezone("Europe/London");

    expect(result.success).toBe(false);
    expect(result.error).toBe("Network error");
  });

  it("returns generic message when error is not an Error instance", async () => {
    mockAuth.mockResolvedValueOnce({
      user: { id: "user-123" },
      expires: "",
    } as never);
    mockFetch.mockRejectedValueOnce("string error");

    const result = await updateTimezone("Europe/London");

    expect(result.success).toBe(false);
    expect(result.error).toBe("Failed to update timezone");
  });
});
