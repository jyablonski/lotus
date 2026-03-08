import { MatchersV3 } from "@pact-foundation/pact";
import { createPact } from "./pactSetup";

const { like, eachLike } = MatchersV3;

const provider = createPact();

describe("Frontend -> Backend: Feature Flag API Contract", () => {
  describe("GET /v1/feature-flags - Get Feature Flags", () => {
    it("returns feature flags for a user role", async () => {
      await provider
        .given("feature flags exist")
        .uponReceiving("a request to get feature flags for a role")
        .withRequest({
          method: "GET",
          path: "/v1/feature-flags",
          query: {
            user_role: like("Consumer"),
          },
        })
        .willRespondWith({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            flags: eachLike({
              name: like("dark_mode"),
              isActive: like(true),
            }),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/v1/feature-flags?user_role=Consumer`,
          {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          },
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(Array.isArray(data.flags)).toBe(true);
        expect(data.flags.length).toBeGreaterThan(0);

        const flag = data.flags[0];
        expect(typeof flag.name).toBe("string");
        expect(typeof flag.isActive).toBe("boolean");
      });
    });
  });
});
