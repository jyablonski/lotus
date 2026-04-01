import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { canAccessAdminRoutes, fetchProfileStats } from "@/lib/server";
import { ProfilePageClient } from "@/components/profile/ProfilePageClient";
import { ROUTES } from "@/lib/routes";

export default async function ProfilePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const email = session.user?.email ?? "No Email Provided";
  // Prefer the OAuth-provided name; fall back to the email prefix so
  // magic-link users see something meaningful instead of "Unknown User".
  const name =
    session.user?.name ||
    (email !== "No Email Provided" ? email.split("@")[0] : "Unknown User");
  const image = session.user?.image ?? null;
  const signUpDate = session.user?.createdAt ?? "";
  const timezone = session.user?.timezone ?? "UTC";

  const [stats, showAdminUI] = await Promise.all([
    fetchProfileStats(session.user.id),
    canAccessAdminRoutes(session.user.email, session.user.role),
  ]);

  return (
    <ProfilePageClient
      name={name}
      email={email}
      image={image}
      signupDate={signUpDate}
      stats={stats}
      isAdmin={showAdminUI}
      timezone={timezone}
    />
  );
}
