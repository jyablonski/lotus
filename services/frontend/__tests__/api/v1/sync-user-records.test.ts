/**
 * Tests for app/api/v1/sync-user-records/route.ts
 *
 * Unit tests for the sync-user-records example API endpoint.
 *
 * @jest-environment node
 */

import { NextRequest } from "next/server";

import { POST } from "@/app/api/v1/sync-user-records/route";

function mockRequest(body: unknown): NextRequest {
  return new NextRequest("http://localhost:3000/api/v1/sync-user-records", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("POST /api/v1/sync-user-records", () => {
  beforeEach(() => {
    jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("returns 200 with ok and user_id when request is valid", async () => {
    const req = mockRequest({ user_id: "user-123" });
    const res = await POST(req);

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json).toEqual({ ok: true, user_id: "user-123" });
    expect(console.log).toHaveBeenCalledWith(
      "[sync-user-records] Request received for user_id: user-123",
    );
  });

  test("returns 400 when user_id is missing", async () => {
    const req = mockRequest({});
    const res = await POST(req);

    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.error).toBe("Invalid request");
    expect(json.details).toBeDefined();
  });

  test("returns 400 when user_id is not a string", async () => {
    const req = mockRequest({ user_id: 123 });
    const res = await POST(req);

    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.error).toBe("Invalid request");
  });

  test("returns 400 when body is invalid JSON", async () => {
    const req = new NextRequest(
      "http://localhost:3000/api/v1/sync-user-records",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "not valid json {{{",
      },
    );
    const res = await POST(req);

    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.error).toBe("Invalid JSON body");
  });
});
