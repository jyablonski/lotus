// auth.ts
import NextAuth, { type User } from "next-auth";
import GitHub from "next-auth/providers/github";
import { NextAuthConfig } from "next-auth";

async function createUserInBackend(email: string, oauthProvider?: string) {
  try {
    const response = await fetch(`${process.env.BACKEND_URL}/v1/oauth/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, oauth_provider: oauthProvider }),
    });
    if (!response.ok) {
      console.error("Error creating user in backend:", response.status);
      return null;
    }
    const data = await response.json();
    return data?.userId; // Extract the userId from the response
  } catch (error) {
    console.error("Error creating user in backend:", error);
    return null;
  }
}

async function fetchBackendUser(email: string) {
  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/v1/users?email=${encodeURIComponent(email)}`
    );
    if (!response.ok) {
      if (response.status === 404) {
        return null; // User not found
      }
      console.error("Error fetching user from backend:", response.status);
      return null;
    }
    const data = await response.json();
    return data; // Return the entire data object
  } catch (error) {
    console.error("Error fetching user from backend:", error);
    return null;
  }
}

export const authConfig: NextAuthConfig = {
  providers: [
    GitHub({ clientId: process.env.GITHUB_ID, clientSecret: process.env.GITHUB_SECRET }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      // Check if the user exists in your backend
      const existingUser = await fetchBackendUser(user.email!);
      console.log("Existing User:", existingUser); // Log the result

      if (!existingUser) {
        console.log("User not found in backend, creating new user...");
        const newUserResult = await createUserInBackend(
          user.email!,
          account?.provider
        );

        if (!newUserResult?.userId) {
          return false;
        }

        (user as User).backendId = newUserResult.userId;
        (user as User).createdAt = newUserResult.createdAt; // Store createdAt
      } else {
        (user as User).backendId = existingUser.userId;
        (user as User).createdAt = existingUser.createdAt; // Store createdAt
      }

      return true;
    },
    async jwt({ token, user }) {
      if (user?.backendId) {
        token.backendId = user.backendId;
      }
      if (user?.createdAt) {
        token.createdAt = user.createdAt; // Optionally persist to JWT
      }
      return token;
    },
    async session({ session, token, user }) {
      if (token?.backendId) {
        session.user.id = token.backendId as string;
      }
      if (token?.createdAt) {
        session.user.createdAt = token.createdAt as string; // Retrieve from JWT
      } else if (user?.createdAt) {
        session.user.createdAt = (user as User).createdAt; // Fallback if not in JWT (shouldn't happen if persisted)
      }
      return session;
    },
  },
};

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);