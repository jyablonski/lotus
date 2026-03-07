import Navbar from "@/components/Navbar";
import { MaintenanceBanner } from "@/components/MaintenanceBanner";
import { auth } from "@/auth";
import { fetchFeatureFlags } from "@/lib/server";
import React from "react";

export default async function Layout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const session = await auth();
  const userRole = session?.user?.role ?? "";
  const flags = await fetchFeatureFlags(userRole);

  return (
    <main className="font-work-sans">
      <Navbar />
      {flags.frontend_maintenance && <MaintenanceBanner />}
      {children}
    </main>
  );
}
