/**
 * Typed route constants for the application.
 * Use these instead of hardcoded route strings to catch broken links at compile time.
 */
export const ROUTES = {
  home: "/",
  signin: "/signin",
  verifyRequest: "/verify-request",
  journal: {
    home: "/journal/home",
    create: "/journal/create",
    calendar: "/journal/calendar",
    detail: (id: string | number) => `/journal/${id}`,
  },
  profile: "/profile",
  profileSettings: "/profile/settings",
  games: {
    csgodouble: "/games/csgodouble",
  },
  admin: "/admin",
  errorDemo: "/error-demo",
} as const;

/** @deprecated Use ROUTES.journal.detail */
export function journalDetailRoute(journalId: string | number): string {
  return ROUTES.journal.detail(journalId);
}
