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
  },
  profile: "/profile",
  profileSettings: "/profile/settings",
  games: {
    csgodouble: "/games/csgodouble",
  },
  admin: "/admin",
  adminInvoices: "/admin/invoices",
  adminCsgodouble: "/admin/csgodouble",
  errorDemo: "/error-demo",
} as const;

/** Helper to build a journal detail route (currently unused, placeholder for future). */
export function journalDetailRoute(journalId: string | number): string {
  return `/journal/${journalId}`;
}
