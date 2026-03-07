import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchProfileStats, fetchFeatureFlags } from "@/lib/server";
import { ProfilePageClient } from "@/components/profile/ProfilePageClient";

export default async function ProfilePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const name = session.user?.name ?? "Unknown User";
  const email = session.user?.email ?? "No Email Provided";
  const image = session.user?.image ?? null;
  const signUpDate = session.user?.createdAt ?? new Date().toISOString();
  const userRole = session.user?.role ?? "";

  // Fetch profile stats and feature flags server-side in parallel
  const [stats, flags] = await Promise.all([
    fetchProfileStats(session.user.id),
    fetchFeatureFlags(userRole),
  ]);

  return (
    <ProfilePageClient
      name={name}
      email={email}
      image={image}
      signupDate={signUpDate}
      stats={stats}
      isAdmin={flags.frontend_admin ?? false}
    />
  );
}
