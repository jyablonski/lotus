import "next-auth";

declare module "next-auth" {
  interface User {
    backendId?: string;
    createdAt?: string;
    role?: string;
    timezone?: string;
  }

  interface Session {
    user: {
      id: string;
      backendId?: string;
      createdAt?: string;
      role?: string;
      timezone?: string;
    } & DefaultSession["user"];
  }

  interface Account {
    provider: string;
    type: string;
    providerAccountId: string | number;
  }

  interface JWT {
    backendId?: string;
    createdAt?: string;
    role?: string;
    timezone?: string;
  }
}
