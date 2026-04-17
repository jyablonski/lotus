"use client";

import { useSession } from "next-auth/react";
import { useEffect } from "react";

/**
 * Sets GA4 user_id and user_properties when the user is authenticated.
 *
 * This is the Next.js equivalent of the Django template block that
 * conditionally injects `gtag('set', ...)` for logged-in users.
 *
 * Uses the internal database user ID (session.user.id) — never PII.
 */
export function AnalyticsUserProperties() {
  const { data: session } = useSession();

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      typeof window.gtag !== "function" ||
      !session?.user?.id
    ) {
      return;
    }

    window.gtag("set", { user_id: session.user.id } as never);

    let daysSinceSignup = 0;
    if (session.user.createdAt) {
      const signupDate = new Date(session.user.createdAt);
      const now = new Date();
      daysSinceSignup = Math.floor(
        (now.getTime() - signupDate.getTime()) / (1000 * 60 * 60 * 24),
      );
    }

    window.gtag(
      "set",
      "user_properties" as never,
      {
        days_since_signup: daysSinceSignup,
      } as never,
    );
  }, [session]);

  return null;
}
