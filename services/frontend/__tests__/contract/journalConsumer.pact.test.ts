import { MatchersV3 } from "@pact-foundation/pact";
import { createPact } from "./pactSetup";

const { like, eachLike } = MatchersV3;

const provider = createPact();

describe("Frontend -> Backend: Journal API Contract", () => {
  describe("POST /v1/journals - Create Journal", () => {
    it("creates a journal entry and returns the journal ID", async () => {
      await provider
        .given("a user exists")
        .uponReceiving("a request to create a journal")
        .withRequest({
          method: "POST",
          path: "/v1/journals",
          headers: { "Content-Type": "application/json" },
          body: {
            user_id: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
            journal_text: like("Today was a great day!"),
            user_mood: like("8"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            journalId: like("123"),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(`${mockServer.url}/v1/journals`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: "a91b114d-b3de-4fe6-b162-039c9850c06b",
            journal_text: "Today was a great day!",
            user_mood: "8",
          }),
        });

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(data.journalId).toBeDefined();
        expect(typeof data.journalId).toBe("string");
      });
    });
  });

  describe("GET /v1/journals - Get Journals", () => {
    it("returns paginated journal entries for a user", async () => {
      await provider
        .given("a user has journal entries")
        .uponReceiving("a request to get journals with pagination")
        .withRequest({
          method: "GET",
          path: "/v1/journals",
          query: {
            user_id: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
            limit: like("10"),
            offset: like("0"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            journals: eachLike({
              journalId: like("1"),
              userId: like("a91b114d-b3de-4fe6-b162-039c9850c06b"),
              journalText: like("Today was a great day!"),
              userMood: like("8"),
              createdAt: like("2026-01-15T10:00:00Z"),
            }),
            totalCount: like("5"),
            hasMore: like(false),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/journals?user_id=a91b114d-b3de-4fe6-b162-039c9850c06b&limit=10&offset=0`,
          {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();

        expect(Array.isArray(data.journals)).toBe(true);
        expect(data.journals.length).toBeGreaterThan(0);

        const journal = data.journals[0];
        expect(typeof journal.journalId).toBe("string");
        expect(typeof journal.userId).toBe("string");
        expect(typeof journal.journalText).toBe("string");
        expect(typeof journal.userMood).toBe("string"); // Backend returns string, frontend parseInt's it
        expect(typeof journal.createdAt).toBe("string");

        // totalCount is returned as a string by the gRPC gateway
        expect(typeof data.totalCount).toBe("string");
        expect(typeof data.hasMore).toBe("boolean");
      });
    });
  });
});
