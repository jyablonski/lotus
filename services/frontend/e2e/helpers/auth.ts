/**
 * Auth helpers for Playwright e2e tests.
 *
 * Creates a valid NextAuth v5 JWT session cookie so tests can
 * bypass GitHub OAuth and act as an authenticated user.
 *
 * Requires AUTH_SECRET env var (same value the running frontend uses).
 */
import { encode } from "next-auth/jwt";
import { type BrowserContext, type Page } from "@playwright/test";

// Cookie name NextAuth v5 uses in non-HTTPS (local dev) mode.
// In production (HTTPS) it would be "__Secure-authjs.session-token".
const SESSION_COOKIE_NAME = "authjs.session-token";

// Must match the salt NextAuth uses internally (same as cookie name).
const SALT = SESSION_COOKIE_NAME;

interface TestUser {
  id: string; // backend user UUID
  name: string;
  email: string;
  image?: string;
  role?: string;
  createdAt?: string;
}

/**
 * Default test user. The `id` here is the backendId that gets placed
 * into session.user.id by the NextAuth session callback.
 */
export const TEST_USER: TestUser = {
  id: "e2e-test-user-00000000-0000-0000-0000-000000000001",
  name: "E2E Test User",
  email: "e2e-test@lotus.dev",
  image: "https://avatars.githubusercontent.com/u/1?v=4",
  role: "Consumer",
  createdAt: "2025-01-01T00:00:00Z",
};

function getAuthSecret(): string {
  const secret = process.env.AUTH_SECRET;
  if (!secret) {
    throw new Error(
      "AUTH_SECRET env var is required for e2e auth. " +
        "Set it to the same value the frontend uses.",
    );
  }
  return secret;
}

/**
 * Generate an encoded NextAuth v5 JWT for the given user.
 */
async function createSessionToken(user: TestUser): Promise<string> {
  const secret = getAuthSecret();

  const token = await encode({
    token: {
      sub: user.id,
      name: user.name,
      email: user.email,
      picture: user.image,
      backendId: user.id,
      role: user.role,
      createdAt: user.createdAt,
    },
    secret,
    salt: SALT,
  });

  return token;
}

/**
 * Inject an authenticated session cookie into a Playwright BrowserContext.
 * Call this *before* navigating to any page.
 *
 * Usage:
 *   test.beforeEach(async ({ context }) => {
 *     await authenticateContext(context);
 *   });
 */
export async function authenticateContext(
  context: BrowserContext,
  user: TestUser = TEST_USER,
): Promise<void> {
  const token = await createSessionToken(user);
  const baseURL = process.env.BASE_URL || "http://localhost:3000";
  const url = new URL(baseURL);

  await context.addCookies([
    {
      name: SESSION_COOKIE_NAME,
      value: token,
      domain: url.hostname,
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
}

/**
 * Convenience: authenticate and then navigate to a page.
 */
export async function authenticateAndGoto(
  page: Page,
  path: string,
  user: TestUser = TEST_USER,
): Promise<void> {
  await authenticateContext(page.context(), user);
  await page.goto(path);
}
