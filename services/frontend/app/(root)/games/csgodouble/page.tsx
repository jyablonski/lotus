import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/routes";

/** Old URL — CSGO Double lives under Admin. */
export default function CsgodoubleLegacyRedirect() {
  redirect(ROUTES.adminCsgodouble);
}
