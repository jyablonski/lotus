import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/routes";
import { fetchFeatureFlags } from "@/lib/server";
import { CsgodoubleGame } from "@/components/profile/CsgodoubleGame";
import Link from "next/link";

export default async function CsgodoublePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const userRole = session.user?.role ?? "";
  const flags = await fetchFeatureFlags(userRole);
  if (!flags.frontend_admin) {
    redirect(ROUTES.profile);
  }

  return (
    <div className="page-container">
      <div className="content-container py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="heading-1">CSGO Double</h1>
          <Link
            href={ROUTES.profile}
            className="text-lotus-400 hover:text-lotus-300 text-sm font-medium"
          >
            ← Back to Profile
          </Link>
        </div>
        <CsgodoubleGame />
      </div>
    </div>
  );
}
