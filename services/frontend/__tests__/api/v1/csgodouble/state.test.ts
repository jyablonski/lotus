/**
 * Tests for app/api/v1/csgodouble/state/route.ts
 *
 * @jest-environment node
 */

import { GET } from "@/app/api/v1/csgodouble/state/route";

const mockGet = jest.fn();
const mockSet = jest.fn();

jest.mock("@/lib/server/redis", () => ({
  redis: {
    get: (...args: unknown[]) => mockGet(...args),
    set: (...args: unknown[]) => mockSet(...args),
  },
}));

describe("GET /api/v1/csgodouble/state", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2025-01-15T12:00:00.000Z"));
    mockGet.mockResolvedValue(null);
    mockSet.mockResolvedValue("OK");
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it("returns 200 with nextRollAt and history", async () => {
    const nextRollAt = Date.now() + 45_000;
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at")
        return Promise.resolve(String(nextRollAt));
      if (key === "csgodouble:history")
        return Promise.resolve(JSON.stringify([7, 14, 0]));
      return Promise.resolve(null);
    });

    const res = await GET();

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.nextRollAt).toBe(nextRollAt);
    expect(json.history).toEqual([7, 14, 0]);
    expect(mockSet).not.toHaveBeenCalled();
  });

  it("sets nextRollAt when missing and returns new value", async () => {
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at") return Promise.resolve(null);
      if (key === "csgodouble:history") return Promise.resolve(null);
      return Promise.resolve(null);
    });

    const res = await GET();

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.nextRollAt).toBeGreaterThanOrEqual(Date.now());
    expect(json.history).toEqual([]);
    expect(mockSet).toHaveBeenCalledWith(
      "csgodouble:next_roll_at",
      expect.any(String),
    );
  });

  it("sets nextRollAt when in the past and returns new value", async () => {
    const pastTime = Date.now() - 10_000;
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at")
        return Promise.resolve(String(pastTime));
      if (key === "csgodouble:history")
        return Promise.resolve(JSON.stringify([3]));
      return Promise.resolve(null);
    });

    const res = await GET();

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.nextRollAt).toBeGreaterThanOrEqual(Date.now());
    expect(json.history).toEqual([3]);
    expect(mockSet).toHaveBeenCalledWith(
      "csgodouble:next_roll_at",
      expect.any(String),
    );
  });

  it("returns empty history when redis has none", async () => {
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at")
        return Promise.resolve(String(Date.now() + 30_000));
      if (key === "csgodouble:history") return Promise.resolve(null);
      return Promise.resolve(null);
    });

    const res = await GET();
    const json = await res.json();
    expect(json.history).toEqual([]);
  });

  it("returns 500 when redis throws", async () => {
    mockGet.mockRejectedValue(new Error("redis connection failed"));

    const res = await GET();

    expect(res.status).toBe(500);
    const json = await res.json();
    expect(json.error).toBe("Failed to get game state");
  });
});
