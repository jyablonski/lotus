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
      const errorText = await response.text();
      console.error("Error creating user in backend:", response.status, errorText);
      return null;
    }
    const data = await response.json();
    // Handle both camelCase (userId) and snake_case (user_id) from backend
    const userId = data?.userId || data?.user_id;
    if (!userId) {
      console.error("No userId in response:", data);
      return null;
    }
    // Return the userId - we'll fetch full user data after creation
    return { userId };
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
    GitHub({ clientId: process.env.AUTH_GITHUB_ID, clientSecret: process.env.AUTH_GITHUB_SECRET }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      // check if the user exists in the backend
      const existingUser = await fetchBackendUser(user.email!);
      console.log("Existing User:", existingUser); // Log the result

      if (!existingUser) {
        console.log("User not found in backend, creating new user...");
        const newUserResult = await createUserInBackend(
          user.email!,
          account?.provider
        );

        if (!newUserResult?.userId) {
          console.error("Failed to create user or get userId");
          return false;
        }

        // After creating user, fetch the full user data to get createdAt
        const createdUser = await fetchBackendUser(user.email!);
        if (!createdUser) {
          console.error("User created but could not fetch user data");
          return false;
        }

        (user as User).backendId = createdUser.userId || createdUser.user_id;
        (user as User).createdAt = createdUser.createdAt || createdUser.created_at;
      } else {
        (user as User).backendId = existingUser.userId || existingUser.user_id;
        (user as User).createdAt = existingUser.createdAt || existingUser.created_at;
      }

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