import { MatchersV3 } from "@pact-foundation/pact";
import { createPact } from "./pactSetup";

const { like } = MatchersV3;

const provider = createPact();

describe("Frontend -> Backend: User API Contract", () => {
  describe("GET /v1/users - Get User by Email", () => {
    it("returns user details for a given email", async () => {
      await provider
        .given("a user with email exists")
        .uponReceiving("a request to get user by email")
        .withRequest({
          method: "GET",
          path: "/v1/users",
          query: {
            email: like("test@example.com"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            userId: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
            email: like("test@example.com"),
            role: like("Consumer"),
            timezone: like("UTC"),
            createdAt: like("2026-01-15T10:00:00Z"),
            updatedAt: like("2026-01-15T10:00:00Z"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/users?email=test@example.com`,
          {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(typeof data.userId).toBe("string");
        expect(typeof data.email).toBe("string");
        expect(typeof data.role).toBe("string");
        expect(typeof data.timezone).toBe("string");
        expect(typeof data.createdAt).toBe("string");
        expect(typeof data.updatedAt).toBe("string");
      });
    });
  });

  describe("POST /v1/oauth/users - Create OAuth User", () => {
    it("creates an OAuth user and returns the user ID", async () => {
      await provider
        .given("no user with this email exists")
        .uponReceiving("a request to create an OAuth user")
        .withRequest({
          method: "POST",
          path: "/v1/oauth/users",
          headers: { "Content-Type": "application/json" },
          body: {
            email: like("newuser@example.com"),
            oauth_provider: like("github"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            userId: like("b91b114d-b3de-4fe6-b162-039c9850c06b"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(`${mockServer.url}/v1/oauth/users`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: "newuser@example.com",
            oauth_provider: "github",
          }),
        });

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(typeof data.userId).toBe("string");
      });
    });
  });

  describe("PATCH /v1/users/{userId}/timezone - Update Timezone", () => {
    it("updates user timezone and returns updated data", async () => {
      const userId = "a91b114d-b3de-4fe6-b162-039c9850c06b";

      await provider
        .given("a user exists")
        .uponReceiving("a request to update user timezone")
        .withRequest({
          method: "PATCH",
          path: `/v1/users/${userId}/timezone`,
          headers: { "Content-Type": "application/json" },
          body: {
            timezone: like("America/New_York"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            userId: like(userId),
            timezone: like("America/New_York"),
            updatedAt: like("2026-01-15T10:00:00Z"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/users/${userId}/timezone`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ timezone: "America/New_York" }),
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(typeof data.userId).toBe("string");
        expect(typeof data.timezone).toBe("string");
        expect(typeof data.updatedAt).toBe("string");
      });
    });
  });
});
