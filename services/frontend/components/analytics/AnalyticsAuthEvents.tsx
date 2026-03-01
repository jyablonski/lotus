"use client";

import { useSession } from "next-auth/react";
import { useEffect, useRef } from "react";
import { trackEvent } from "@/lib/analytics";

/**
 * Fires `login` and `sign_up` GA4 events by detecting session transitions.
 *
 * Approach: when the session status transitions from "unauthenticated" or
 * "loading" to "authenticated", we treat it as a login event.  We distinguish
 * a brand-new account (sign_up) from a returning login by checking
 * `days_since_signup === 0` (i.e. the account was created today).
 *
 * This component renders nothing — it only exists for its side-effect.
 */
export function AnalyticsAuthEvents() {
  const { data: session, status } = useSession();
  const previousStatus = useRef(status);
  const hasFiredLogin = useRef(false);

  useEffect(() => {
    // Detect transition to "authenticated"
    if (
      status === "authenticated" &&
      previousStatus.current !== "authenticated" &&
      !hasFiredLogin.current &&
      session?.user?.id
    ) {
      hasFiredLogin.current = true;

      // Determine auth method from session — NextAuth doesn't expose the
      // provider on the client session by default, so we use a heuristic:
      // if the user has a GitHub avatar URL, they signed in with GitHub;
      // otherwise they used the email magic link.
      const method = session.user.image?.includes("githubusercontent")
        ? "github"
        : "email";

      // Check if this is a brand-new account (created today)
      if (session.user.createdAt) {
        const signupDate = new Date(session.user.createdAt);
        const now = new Date();
        const daysSinceSignup = Math.floor(
          (now.getTime() - signupDate.getTime()) / (1000 * 60 * 60 * 24),
        );

        if (daysSinceSignup === 0) {
          trackEvent("sign_up", { method });
        }
      }

      trackEvent("login", { method });
    }

    previousStatus.current = status;
  }, [status, session]);

  return null;
}
