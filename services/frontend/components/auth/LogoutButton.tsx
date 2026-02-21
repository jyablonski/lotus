"use client";

import { signOut } from "next-auth/react";
import { LogOut } from "lucide-react";

export function Logout() {
  const handleSignOut = async () => {
    await signOut({ callbackUrl: "/" });
  };

  return (
    <button onClick={handleSignOut} className="btn-danger">
      <LogOut size={20} />
      <span className="font-medium">Sign Out</span>
    </button>
  );
}
