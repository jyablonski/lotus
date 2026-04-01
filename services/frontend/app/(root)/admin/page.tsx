import { auth } from "@/auth";
import Link from "next/link";
import { redirect } from "next/navigation";
import { FileText, Gamepad2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { canAccessAdminRoutes, fetchFeatureFlags } from "@/lib/server";
import { ROUTES } from "@/lib/routes";

export default async function AdminPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  if (!(await canAccessAdminRoutes(session.user.email, session.user.role))) {
    redirect(ROUTES.home);
  }

  const userRole = session.user?.role ?? "";
  const flags = await fetchFeatureFlags(userRole);

  return (
    <div className="page-container">
      <div className="content-container py-8">
        <h1 className="heading-1 mb-2">Admin</h1>
        <p className="text-muted-dark mb-8 max-w-2xl">
          Internal tools. Access matches the profile Admin badge: Admin role or{" "}
          <code className="text-xs bg-dark-800 px-1.5 py-0.5 rounded">
            frontend_admin
          </code>{" "}
          flag, or an optional{" "}
          <code className="text-xs bg-dark-800 px-1.5 py-0.5 rounded">
            ADMIN_EMAILS
          </code>{" "}
          allowlist.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
          <Link href={ROUTES.adminInvoices} className="block group">
            <Card className="h-full transition-colors hover:border-lotus-500/40">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-lotus-500/10 text-lotus-400">
                    <FileText size={22} />
                  </span>
                  <div>
                    <h2 className="text-lg font-semibold text-primary-dark group-hover:text-lotus-300">
                      Invoice generator
                    </h2>
                    <p className="text-sm text-muted-dark mt-0.5">
                      Create and download PDF invoices
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <span className="text-sm text-lotus-400 font-medium">
                  Open →
                </span>
              </CardContent>
            </Card>
          </Link>

          {flags.frontend_admin ? (
            <Link href={ROUTES.adminCsgodouble} className="block group">
              <Card className="h-full transition-colors hover:border-lotus-500/40">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-lotus-500/10 text-lotus-400">
                      <Gamepad2 size={22} />
                    </span>
                    <div>
                      <h2 className="text-lg font-semibold text-primary-dark group-hover:text-lotus-300">
                        CSGO Double
                      </h2>
                      <p className="text-sm text-muted-dark mt-0.5">
                        Wheel game (dev / admin feature flag)
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <span className="text-sm text-lotus-400 font-medium">
                    Open →
                  </span>
                </CardContent>
              </Card>
            </Link>
          ) : (
            <Card className="h-full opacity-60 border-dark-600">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-dark-700 text-dark-400">
                    <Gamepad2 size={22} />
                  </span>
                  <div>
                    <h2 className="text-lg font-semibold text-dark-300">
                      CSGO Double
                    </h2>
                    <p className="text-sm text-muted-dark mt-0.5">
                      Requires the{" "}
                      <code className="text-xs">frontend_admin</code> feature
                      flag for your role.
                    </p>
                  </div>
                </div>
              </CardHeader>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
