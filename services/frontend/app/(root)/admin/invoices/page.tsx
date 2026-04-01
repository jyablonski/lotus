import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/routes";
import { canAccessAdminRoutes, fetchInvoiceReferenceData } from "@/lib/server";
import { InvoiceGeneratorForm } from "@/components/admin/InvoiceGeneratorForm";

export default async function InvoicesPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  if (!(await canAccessAdminRoutes(session.user.email, session.user.role))) {
    redirect(ROUTES.home);
  }

  const referenceData = await fetchInvoiceReferenceData();

  return (
    <div className="page-container">
      <div className="content-container py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="heading-1">Invoice generator</h1>
          <a href={ROUTES.admin} className="btn-outline text-sm">
            Back to Admin
          </a>
        </div>
        <InvoiceGeneratorForm referenceData={referenceData ?? undefined} />
      </div>
    </div>
  );
}
