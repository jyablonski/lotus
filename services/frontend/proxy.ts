import NextAuth from "next-auth";
import { edgeAuthConfig } from "./auth.config";

// Use the Edge-safe config for middleware. This avoids pulling in Node.js-only
// packages (e.g. ioredis) into the Edge runtime bundle. The full config with
// the adapter lives in auth.ts and is only used server-side.
const { auth } = NextAuth(edgeAuthConfig);
export { auth as proxy };
