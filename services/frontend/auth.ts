import NextAuth, { type User } from "next-auth";
import GitHub from "next-auth/providers/github";
import { NextAuthConfig } from "next-auth";

// ---------------------------------------------------------------------------
// Types for backend responses
// ---------------------------------------------------------------------------

/** Response shape from GET /v1/users?email=... */
interface BackendUserResponse {
  userId?: string;
  user_id?: string;
  createdAt?: string;
  created_at?: string;
}

/** Normalized backend user data */
interface BackendUser {
  userId: string;
  createdAt: string | undefined;
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
    const response = await fetch(`${process.env.BACKEND_URL}/v1/oauth/users`, {
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

async function fetchBackendUser(email: string): Promise<BackendUser | null> {
  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/v1/users?email=${encodeURIComponent(email)}`,
    );

    if (!response.ok) {
      if (response.status === 404) return null; // User not found — expected
      authLog("error", "Failed to fetch user from backend", {
        status: response.status,
      });
      return null;
    }

    const data: BackendUserResponse = await response.json();
    return parseBackendUser(data);
  } catch (error) {
    authLog("error", "Network error fetching user from backend", {
      error: error instanceof Error ? error.message : String(error),
    });
    return null;
  }
}

// ---------------------------------------------------------------------------
// NextAuth config
// ---------------------------------------------------------------------------

export const authConfig: NextAuthConfig = {
  providers: [
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID,
      clientSecret: process.env.AUTH_GITHUB_SECRET,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (!user.email) {
        authLog("warn", "Sign-in attempt with no email on the OAuth user");
        return false;
      }

      // Check if user already exists
      let backendUser = await fetchBackendUser(user.email);

      if (!backendUser) {
        // Create the user, then fetch full record for createdAt
        const createResult = await createUserInBackend(
          user.email,
          account?.provider,
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

      return true;
    },

    async jwt({ token, user }) {
      if (user?.backendId) {
        token.backendId = user.backendId;
      }
      if (user?.createdAt) {
        token.createdAt = user.createdAt;
      }
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
      return session;
    },
  },
};

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);
