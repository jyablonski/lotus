import { auth } from "@/auth";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/routes";
import { canAccessAdminRoutes, fetchFeatureFlags } from "@/lib/server";
import { CsgodoubleGame } from "@/components/profile/CsgodoubleGame";

export default async function AdminCsgodoublePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  if (!(await canAccessAdminRoutes(session.user.email, session.user.role))) {
    redirect(ROUTES.home);
  }

  const userRole = session.user?.role ?? "";
  const flags = await fetchFeatureFlags(userRole);
  if (!flags.frontend_admin) {
    redirect(ROUTES.admin);
  }

  return (
    <div className="page-container">
      <div className="content-container py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="heading-1">CSGO Double</h1>
          <Link
            href={ROUTES.admin}
            className="text-lotus-400 hover:text-lotus-300 text-sm font-medium"
          >
            ← Back to Admin
          </Link>
        </div>
        <CsgodoubleGame />
      </div>
    </div>
  );
}
