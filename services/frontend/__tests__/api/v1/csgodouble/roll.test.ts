/**
 * @jest-environment node
 */

const mockRandomInt = jest.fn().mockReturnValue(13);
jest.mock("node:crypto", () => ({
  randomInt: (...args: unknown[]) => mockRandomInt(...args),
  randomBytes: (size: number) =>
    Buffer.from(Array.from({ length: size }, () => 0)),
}));

jest.mock("@/auth", () => ({
  auth: async () => ({ user: { id: "test-user-id" }, expires: "2099-01-01" }),
}));

import { POST } from "@/app/api/v1/csgodouble/roll/route";

const mockGet = jest.fn();
const mockSet = jest.fn();
const mockExec = jest.fn().mockResolvedValue(undefined);
const mockEval = jest.fn().mockResolvedValue(undefined);

jest.mock("@/lib/server/redis", () => ({
  redis: {
    get: (...args: unknown[]) => mockGet(...args),
    set: (...args: unknown[]) => mockSet(...args),
    eval: (...args: unknown[]) => mockEval(...args),
    multi: () => ({
      set: () => ({
        set: () => ({ exec: () => mockExec() }),
      }),
    }),
  },
}));

describe("POST /api/v1/csgodouble/roll", () => {
  const originalNow = Date.now;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2025-01-15T12:00:00.000Z"));
    mockGet.mockResolvedValue(null);
    mockSet.mockResolvedValue("OK");
    mockExec.mockResolvedValue(undefined);
    mockRandomInt.mockReturnValue(13);
  });

  afterEach(() => {
    jest.useRealTimers();
    Date.now = originalNow;
    jest.restoreAllMocks();
  });

  it("returns 429 when roll is too early", async () => {
    const nextRollAt = Date.now() + 30_000;
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at")
        return Promise.resolve(String(nextRollAt));
      if (key === "csgodouble:history") return Promise.resolve(null);
      return Promise.resolve(null);
    });

    const res = await POST();

    expect(res.status).toBe(429);
    const json = await res.json();
    expect(json.error).toBe("Too early to roll");
    expect(json.nextRollAt).toBe(nextRollAt);
    expect(mockExec).not.toHaveBeenCalled();
  });

  it("returns 200 with result, nextRollAt, and history when allowed to roll", async () => {
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at") return Promise.resolve(null);
      if (key === "csgodouble:history")
        return Promise.resolve(JSON.stringify([10, 5]));
      return Promise.resolve(null);
    });

    const res = await POST();

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.result).toBe(13);
    expect(json.nextRollAt).toBeGreaterThanOrEqual(Date.now());
    expect(json.history).toEqual([13, 10, 5]);
    expect(mockRandomInt).toHaveBeenCalledWith(0, 15);
    expect(mockExec).toHaveBeenCalled();
  });

  it("returns result in range 0..14", async () => {
    mockRandomInt.mockReturnValue(0);
    const res = await POST();
    const json = await res.json();
    expect(json.result).toBe(0);

    mockRandomInt.mockReturnValue(14);
    const res2 = await POST();
    const json2 = await res2.json();
    expect(json2.result).toBe(14);
  });

  it("caps history at 10 entries", async () => {
    const longHistory = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    mockGet.mockImplementation((key: string) => {
      if (key === "csgodouble:next_roll_at") return Promise.resolve(null);
      if (key === "csgodouble:history")
        return Promise.resolve(JSON.stringify(longHistory));
      return Promise.resolve(null);
    });

    const res = await POST();
    const json = await res.json();
    expect(json.history).toHaveLength(10);
    expect(json.history[0]).toBe(13);
  });

  it("returns 500 when redis throws", async () => {
    mockGet.mockRejectedValue(new Error("redis connection failed"));

    const res = await POST();

    expect(res.status).toBe(500);
    const json = await res.json();
    expect(json.error).toBe("Failed to roll");
  });
});
