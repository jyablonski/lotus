import NextAuth, { type User } from "next-auth";
import GitHub from "next-auth/providers/github";
import Resend from "next-auth/providers/resend";
import { NextAuthConfig } from "next-auth";
import type {
  Adapter,
  AdapterUser,
  VerificationToken,
} from "@auth/core/adapters";
import { BACKEND_URL } from "@/lib/config";
import { ROUTES } from "@/lib/routes";
import { redis } from "@/lib/server/redis";

// ---------------------------------------------------------------------------
// Types for backend responses
// ---------------------------------------------------------------------------

/** Response shape from GET /v1/users?email=... */
interface BackendUserResponse {
  userId?: string;
  user_id?: string;
  createdAt?: string;
  created_at?: string;
  role?: string;
  timezone?: string;
}

/** Normalized backend user data */
interface BackendUser {
  userId: string;
  createdAt: string | undefined;
  role: string | undefined;
  timezone: string;
}

/** Response shape from POST /v1/oauth/users */
interface CreateUserResponse {
  userId?: string;
  user_id?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseBackendUser(data: BackendUserResponse): BackendUser | null {
  const userId = data.userId || data.user_id;
  if (!userId) return null;
  return {
    userId,
    createdAt: data.createdAt || data.created_at,
    role: data.role,
    timezone: data.timezone || "UTC",
  };
}

/** Server-side structured log (JSON for production, readable for dev). */
function authLog(
  level: "info" | "warn" | "error",
  msg: string,
  meta?: Record<string, unknown>,
) {
  const entry = { ts: new Date().toISOString(), level, msg, ...meta };
  if (level === "error") {
    console.error(JSON.stringify(entry));
  } else {
    console.log(JSON.stringify(entry));
  }
}

// ---------------------------------------------------------------------------
// Backend API calls
// ---------------------------------------------------------------------------

async function createUserInBackend(
  email: string,
  oauthProvider?: string,
): Promise<{ userId: string } | null> {
  try {
    const response = await fetch(`${BACKEND_URL}/v1/oauth/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, oauth_provider: oauthProvider }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      authLog("error", "Failed to create user in backend", {
        status: response.status,
        body: errorText,
      });
      return null;
    }

    const data: CreateUserResponse = await response.json();
    const userId = data.userId || data.user_id;

    if (!userId) {
      authLog("error", "Backend create-user response missing userId", { data });
      return null;
    }

    return { userId };
  } catch (error) {
    authLog("error", "Network error creating user in backend", {
      error: error instanceof Error ? error.message : String(error),
    });
    return null;
  }
}

// Short TTL cache to avoid multiple GetUser calls per page load when
// layout, page, Navbar, etc. each call auth() and the JWT callback runs.
const USER_CACHE_TTL_MS = 2000; // 2 seconds
const userCache = new Map<string, { user: BackendUser; until: number }>();

// Coalesce in-flight requests: concurrent callers for the same email
// share one backend request instead of each firing their own.
const inFlight = new Map<string, Promise<BackendUser | null>>();

async function fetchBackendUser(email: string): Promise<BackendUser | null> {
  const now = Date.now();
  const hit = userCache.get(email);
  if (hit && hit.until > now) {
    return hit.user;
  }

  let promise = inFlight.get(email);
  if (promise) {
    return promise;
  }

  promise = (async () => {
    try {
      const response = await fetch(
        `${BACKEND_URL}/v1/users?email=${encodeURIComponent(email)}`,
      );

      if (!response.ok) {
        if (response.status === 404) return null; // User not found — expected
        authLog("error", "Failed to fetch user from backend", {
          status: response.status,
        });
        return null;
      }

      const data: BackendUserResponse = await response.json();
      const user = parseBackendUser(data);
      if (user) {
        userCache.set(email, { user, until: Date.now() + USER_CACHE_TTL_MS });
      }
      return user;
    } catch (error) {
      authLog("error", "Network error fetching user from backend", {
        error: error instanceof Error ? error.message : String(error),
      });
      return null;
    } finally {
      inFlight.delete(email);
    }
  })();

  inFlight.set(email, promise);
  return promise;
}

// ---------------------------------------------------------------------------
// Minimal adapter for the email (magic link) provider
// ---------------------------------------------------------------------------
// NextAuth's email provider requires: getUserByEmail, createUser,
// createVerificationToken, and useVerificationToken.
//
// User CRUD is delegated to the Go backend via HTTP. Verification tokens are
// stored in Redis so they survive container restarts and work across replicas.
// ---------------------------------------------------------------------------

function tokenKey(identifier: string, token: string) {
  return `nextauth:vtoken:${identifier}:${token}`;
}

function toAdapterUser(
  email: string,
  backendUser: BackendUser | null,
): AdapterUser {
  return {
    id: backendUser?.userId ?? email, // use backend UUID when available
    email,
    emailVerified: backendUser ? new Date() : null,
  };
}

const magicLinkAdapter: Adapter = {
  // -- User methods (backed by Go backend) ----------------------------------

  async getUserByEmail(email: string) {
    const backendUser = await fetchBackendUser(email);
    if (!backendUser) return null;
    return toAdapterUser(email, backendUser);
  },

  async createUser(user: AdapterUser) {
    // Create the user in the Go backend then return an AdapterUser.
    const result = await createUserInBackend(user.email, "email");
    if (!result) {
      throw new Error(`Failed to create user in backend for ${user.email}`);
    }
    const backendUser = await fetchBackendUser(user.email);
    return toAdapterUser(user.email, backendUser);
  },

  async getUser(id: string) {
    // Not used with JWT strategy, but return null to satisfy the interface.
    return null;
  },

  async getUserByAccount() {
    // Not used — account linking is handled by our signIn callback.
    return null;
  },

  async updateUser(user) {
    // No-op: we don't update users through NextAuth.
    return user as AdapterUser;
  },

  async linkAccount() {
    // No-op: account linking is managed by our signIn callback.
    return undefined;
  },

  // -- Verification token methods (Redis) -----------------------------------

  async createVerificationToken(verificationToken: VerificationToken) {
    const key = tokenKey(verificationToken.identifier, verificationToken.token);
    const ttlSeconds = Math.ceil(
      (new Date(verificationToken.expires).getTime() - Date.now()) / 1000,
    );
    await redis.set(key, JSON.stringify(verificationToken), "EX", ttlSeconds);
    return verificationToken;
  },

  async useVerificationToken({
    identifier,
    token,
  }: {
    identifier: string;
    token: string;
  }) {
    const key = tokenKey(identifier, token);
    const raw = await redis.get(key);
    if (!raw) return null;
    await redis.del(key);
    const stored = JSON.parse(raw) as VerificationToken;
    return { ...stored, expires: new Date(stored.expires) };
  },
};

// ---------------------------------------------------------------------------
// NextAuth config
// ---------------------------------------------------------------------------

/** Clears the backend-user cache and in-flight map. Used by tests to avoid cross-test pollution. */
export function __clearBackendUserCacheForTests(): void {
  userCache.clear();
  inFlight.clear();
}

export const authConfig: NextAuthConfig = {
  adapter: magicLinkAdapter,
  // Keep using JWT strategy — the adapter is only needed for verification
  // tokens (magic link). We do NOT use database sessions.
  session: { strategy: "jwt" },
  pages: {
    signIn: ROUTES.signin,
    verifyRequest: ROUTES.verifyRequest,
  },
  providers: [
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID,
      clientSecret: process.env.AUTH_GITHUB_SECRET,
      // Allow users who originally signed in via magic link (Resend) to
      // later sign in with GitHub using the same verified email address.
      // Safe because GitHub verifies email ownership.
      allowDangerousEmailAccountLinking: true,
    }),
    Resend({
      apiKey: process.env.AUTH_RESEND_KEY,
      from: process.env.AUTH_EMAIL_FROM || "Lotus <onboarding@resend.dev>",
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (!user.email) {
        authLog("warn", "Sign-in attempt with no email");
        return false;
      }

      // For the email provider, the signIn callback fires twice:
      //   1. When the email is sent (account.type === "email") — allow it
      //      through so the verification email is dispatched.
      //   2. When the user clicks the magic link — the callback fires again
      //      with the verified user. At that point we sync with the backend.
      //
      // We detect phase-1 by checking if the user has no `id` yet (NextAuth
      // hasn't resolved the user from the adapter).  In that case we simply
      // return true to let the email be sent.
      const isEmailProvider = account?.provider === "resend";

      // Phase-1 of email sign-in: enforce a per-email cooldown, then allow.
      if (isEmailProvider && !user.id) {
        const cooldownKey = `nextauth:signin-cooldown:${user.email}`;
        const inCooldown = await redis.get(cooldownKey);
        if (inCooldown) {
          authLog("warn", "Magic-link sign-in rate limited", {
            email: user.email,
          });
          return false;
        }
        await redis.set(cooldownKey, "1", "EX", 60);
        return true;
      }

      // ----- Backend user sync (runs for GitHub and magic-link phase-2) -----
      let backendUser = await fetchBackendUser(user.email);

      if (!backendUser) {
        // Create the user in the Go backend.
        // For email sign-ins we pass "email" as the oauth_provider value
        // to distinguish them from GitHub-authenticated users.
        const providerLabel = isEmailProvider ? "email" : account?.provider;
        const createResult = await createUserInBackend(
          user.email,
          providerLabel,
        );
        if (!createResult?.userId) {
          authLog(
            "error",
            "Failed to create user or get userId — blocking sign-in",
          );
          return false;
        }

        backendUser = await fetchBackendUser(user.email);
        if (!backendUser) {
          authLog(
            "error",
            "User created but could not fetch user data — blocking sign-in",
          );
          return false;
        }
      }

      // Attach backend fields to the NextAuth user object
      (user as User).backendId = backendUser.userId;
      (user as User).createdAt = backendUser.createdAt;
      (user as User).role = backendUser.role;
      (user as User).timezone = backendUser.timezone;

      return true;
    },

    async jwt({ token, user, account, trigger, session }) {
      // When client calls session.update(), trigger is "update" and session
      // contains the new data. Use it to refresh timezone without re-login.
      if (trigger === "update" && session) {
        const newTimezone =
          (session as { timezone?: string }).timezone ??
          (session as { user?: { timezone?: string } }).user?.timezone;
        if (newTimezone !== undefined) {
          token.timezone = newTimezone;
        }
      }

      // On initial sign-in the `user` object is populated.
      if (user) {
        if (user.backendId) {
          token.backendId = user.backendId;
        } else if (user.id) {
          // For email sign-ins, the adapter's getUserByEmail already returned
          // the backend UUID as the AdapterUser.id — use it directly.
          token.backendId = user.id;
        }
        if (user.createdAt) {
          token.createdAt = user.createdAt;
        }
        if (user.role) {
          token.role = user.role;
        }
        if (user.timezone) {
          token.timezone = user.timezone;
        }
        // Persist the email on the token so we can resolve backendId later.
        if (user.email) {
          token.email = user.email;
        }
        // Persist the name (only OAuth providers like GitHub supply one).
        if (user.name) {
          token.name = user.name;
        }

        // NextAuth may pass a fresh OAuth profile to jwt() that doesn't include
        // our signIn mutations (backendId, role, etc.). Ensure role is set
        // from the backend when we have email so Admin users get the correct role.
        if (!token.role && user.email) {
          const backendUser = await fetchBackendUser(user.email);
          if (backendUser) {
            token.role = backendUser.role;
            if (!token.backendId) token.backendId = backendUser.userId;
            if (!token.createdAt) token.createdAt = backendUser.createdAt;
            if (!token.timezone) token.timezone = backendUser.timezone;
          }
        }
      }

      const email = (token.email as string) || undefined;

      // If backendId is still missing (common with email/magic-link sign-ins
      // where the adapter user object doesn't carry our custom fields), look
      // it up from the Go backend by email.
      if (!token.backendId && email) {
        const backendUser = await fetchBackendUser(email);
        if (backendUser) {
          token.backendId = backendUser.userId;
          token.createdAt = backendUser.createdAt;
          token.role = backendUser.role;
          token.timezone = backendUser.timezone;
        } else {
          // User doesn't exist yet — create them.
          const result = await createUserInBackend(email, "email");
          if (result) {
            const created = await fetchBackendUser(email);
            if (created) {
              token.backendId = created.userId;
              token.createdAt = created.createdAt;
              token.role = created.role;
              token.timezone = created.timezone;
            }
          }
        }
      }

      // Rely on the JWT for role, timezone, createdAt after login. No backend
      // call here — best practice for JWT auth. Role/timezone changes (e.g.
      // admin promotion) take effect on next sign-in, or add a "Refresh session"
      // flow if you need them without re-login.

      return token;
    },

    async session({ session, token, user }) {
      if (token?.backendId) {
        session.user.id = token.backendId as string;
      }
      if (token?.createdAt) {
        session.user.createdAt = token.createdAt as string;
      } else if (user?.createdAt) {
        session.user.createdAt = (user as User).createdAt;
      }
      if (token?.role) {
        session.user.role = token.role as string;
      }
      if (token?.timezone) {
        session.user.timezone = token.timezone as string;
      }
      // Explicitly propagate name and email from the JWT token.
      // NextAuth's default mapping usually handles this, but being
      // explicit avoids silent breakage (e.g. magic-link users).
      if (token?.name) {
        session.user.name = token.name as string;
      }
      if (token?.email) {
        session.user.email = token.email as string;
      }
      return session;
    },
  },
};

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);
