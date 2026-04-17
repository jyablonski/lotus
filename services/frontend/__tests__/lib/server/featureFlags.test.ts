jest.mock("@/lib/config", () => ({
  BACKEND_URL: "http://backend:8080",
  BACKEND_API_KEY: "test-api-key",
}));

import { fetchFeatureFlags } from "@/lib/server/featureFlags";

const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("fetchFeatureFlags", () => {
  it("returns flags map when backend returns flags array", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          flags: [
            { name: "frontend_maintenance", isActive: true },
            { name: "frontend_admin", isActive: false },
          ],
        }),
    });

    const result = await fetchFeatureFlags();

    expect(result).toEqual({
      frontend_maintenance: true,
      frontend_admin: false,
    });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/v1\/feature-flags/),
      expect.any(Object),
    );
  });

  it("appends userRole query param when provided (camelCase for gRPC-Gateway)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ flags: [] }),
    });

    await fetchFeatureFlags("Admin");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("userRole=Admin"),
      expect.any(Object),
    );
  });

  it("sends Authorization Bearer header on every request", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ flags: [] }),
    });

    await fetchFeatureFlags();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-api-key",
        }),
      }),
    );
  });

  it("returns empty object when response is not ok", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    const result = await fetchFeatureFlags();

    expect(result).toEqual({});
  });

  it("returns empty object when response has no flags array", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });

    const result = await fetchFeatureFlags();

    expect(result).toEqual({});
  });

  it("returns empty object on fetch error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const result = await fetchFeatureFlags();

    expect(result).toEqual({});
  });
});
