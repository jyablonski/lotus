import path from "path";
import {
  Pact,
  Interaction,
  Matchers,
  type PactOptions,
} from "@pact-foundation/pact";

export const PROVIDER_NAME = "LotusBackend";
export const CONSUMER_NAME = "LotusFrontend";
export const PACT_DIR = path.resolve(__dirname, "../../pacts");

/** Pact v9 exports Matchers; contract tests expect MatchersV3 (same API: like, eachLike). */
export const MatchersV3 = Matchers;

interface MockServer {
  url: string;
}

interface PactV3Like {
  given(state: string): this;
  uponReceiving(description: string): this;
  withRequest(request: Record<string, unknown>): this;
  willRespondWith(response: Record<string, unknown>): this;
  executeTest(
    callback: (mockServer: MockServer) => Promise<void>,
  ): Promise<void>;
}

/**
 * Returns a Pact v9-backed wrapper that implements the PactV3-style fluent API
 * and executeTest so existing contract tests work without upgrading to Pact v10.
 */
export function createPact(): PactV3Like {
  let state = "";
  let uponReceivingVal = "";
  let withRequestVal: Record<string, unknown> = {};
  let willRespondWithVal: Record<string, unknown> = {};

  return {
    given(s: string) {
      state = s;
      return this;
    },
    uponReceiving(d: string) {
      uponReceivingVal = d;
      return this;
    },
    withRequest(r: Record<string, unknown>) {
      withRequestVal = r;
      return this;
    },
    willRespondWith(w: Record<string, unknown>) {
      willRespondWithVal = w;
      return this;
    },
    async executeTest(callback: (mockServer: MockServer) => Promise<void>) {
      const opts: PactOptions = {
        consumer: CONSUMER_NAME,
        provider: PROVIDER_NAME,
        dir: PACT_DIR,
      };
      const provider = new Pact(opts);
      await provider.setup();
      const interaction = new Interaction()
        .given(state)
        .uponReceiving(uponReceivingVal)
        .withRequest(
          withRequestVal as unknown as Parameters<
            Interaction["withRequest"]
          >[0],
        )
        .willRespondWith(
          willRespondWithVal as unknown as Parameters<
            Interaction["willRespondWith"]
          >[0],
        );
      await provider.addInteraction(interaction);
      const baseUrl = `http://${provider.opts.host}:${provider.opts.port}`;
      try {
        await callback({ url: baseUrl });
      } finally {
        await provider.verify();
        await provider.finalize();
      }
    },
  };
}
