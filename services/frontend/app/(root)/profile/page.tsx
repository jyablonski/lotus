import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchProfileStats } from "@/lib/server";
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

  // Fetch profile stats server-side
  const stats = await fetchProfileStats(session.user.id);

  return (
    <ProfilePageClient
      name={name}
      email={email}
      image={image}
      signupDate={signUpDate}
      stats={stats}
    />
  );
}
