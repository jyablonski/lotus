import "server-only";

import { fetchFeatureFlags } from "./featureFlags";

/**
 * Explicit allowlist (optional). When unset or empty, other checks still apply.
 */
export function isAdminEmail(email: string | null | undefined): boolean {
  if (!email) return false;
  const allowed =
    process.env.ADMIN_EMAILS?.split(",").map((e) => e.trim().toLowerCase()) ??
    [];
  return allowed.length > 0 && allowed.includes(email.toLowerCase());
}

/** Matches backend / Django `users.role` (e.g. "Admin"). */
export function isAdminRole(role: string | null | undefined): boolean {
  if (!role) return false;
  return role.trim().toLowerCase() === "admin";
}

/**
 * Who may open /admin and invoice tools. Aligns with the profile "Admin"
 * badge (frontend_admin waffle flag) and/or DB Admin role — not ADMIN_EMAILS
 * alone (that env is optional extra allowlisting).
 */
export async function canAccessAdminRoutes(
  email: string | null | undefined,
  role: string | null | undefined,
): Promise<boolean> {
  if (isAdminEmail(email)) return true;
  if (isAdminRole(role)) return true;
  const flags = await fetchFeatureFlags(role ?? "");
  return flags.frontend_admin === true;
}
