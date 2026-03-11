import type { NextAuthConfig } from "next-auth";
import { ROUTES } from "@/lib/routes";

// Minimal auth config used by the middleware (Edge runtime).
// Must not import any Node.js-only packages (e.g. ioredis).
// The full config — including the adapter and Redis — lives in auth.ts and
// is only used in server components, API routes, and server actions.
export const edgeAuthConfig: NextAuthConfig = {
  session: { strategy: "jwt" },
  pages: {
    signIn: ROUTES.signin,
    verifyRequest: ROUTES.verifyRequest,
  },
  providers: [],
};
