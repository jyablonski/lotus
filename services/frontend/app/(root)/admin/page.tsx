import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/routes";

/**
 * Admin page — restricted to allowed admin emails.
 * Set ADMIN_EMAILS env var as a comma-separated list (e.g. "alice@example.com,bob@example.com").
 * If ADMIN_EMAILS is not set, the page is inaccessible to everyone.
 */
function isAdmin(email: string | null | undefined): boolean {
  if (!email) return false;
  const allowed =
    process.env.ADMIN_EMAILS?.split(",").map((e) => e.trim().toLowerCase()) ??
    [];
  return allowed.includes(email.toLowerCase());
}

export default async function AdminPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  if (!isAdmin(session.user.email)) {
    redirect(ROUTES.home);
  }

  // Show only non-sensitive session info
  const safeSessionInfo = {
    id: session.user.id,
    name: session.user.name ?? "N/A",
    email: session.user.email ?? "N/A",
    createdAt: session.user.createdAt ?? "N/A",
  };

  return (
    <div className="page-container">
      <div className="content-container py-8">
        <h1 className="heading-1 mb-6">Admin</h1>
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-primary-dark mb-4">
            Session Info
          </h2>
          <dl className="space-y-2 text-sm">
            {Object.entries(safeSessionInfo).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <dt className="text-muted-dark font-medium">{key}</dt>
                <dd className="text-primary-dark">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
