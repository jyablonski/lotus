import path from "path";
import { PactV3 } from "@pact-foundation/pact";

export const PROVIDER_NAME = "LotusBackend";
export const CONSUMER_NAME = "LotusFrontend";
export const PACT_DIR = path.resolve(__dirname, "../../pacts");

export function createPact(): PactV3 {
  return new PactV3({
    consumer: CONSUMER_NAME,
    provider: PROVIDER_NAME,
    dir: PACT_DIR,
  });
}
