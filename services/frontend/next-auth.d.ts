import "next-auth";

declare module "next-auth" {
  interface User {
    backendId?: string;
    createdAt?: string;
  }

  interface Session {
    user: {
      id: string;
      backendId?: string;
      createdAt?: string;
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
  }
}
