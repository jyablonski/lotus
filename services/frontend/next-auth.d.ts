// src/next-auth.d.ts (or wherever you have this file)

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
            userCreatedAt?: string;
        } & DefaultSession["user"];
    }

    interface Account {
        provider: string;
        type: string;
        providerAccountId: string | number;
    }

    interface JWT {
        backendId?: string;
    }
}