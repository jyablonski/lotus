import Link from "next/link";
import Image from "next/image";
import React from "react";
import { auth, signOut, signIn } from "@/auth";

const Navbar = async () => {
  const session = await auth();

  return (
    <header className="navbar-header">
      <nav className="navbar-container">
        <Link href="/" className="navbar-logo">
          <Image src="/lotus.png" alt="Logo" width={40} height={40} />
          <span className="navbar-logo-text">Lotus</span>
        </Link>

        <div className="navbar-items">
          {session && session.user ? (
            <>
              <Link href="/journal/create" className="navbar-link">
                Create
              </Link>

              <form
                action={async () => {
                  "use server";
                  await signOut({ redirectTo: "/" });
                }}
              >
                <button type="submit" className="navbar-logout-button">
                  Logout
                </button>
              </form>


              <Link href={`/about`} className="navbar-link">
                About
              </Link>

              <Link href={`/profile/hi`} className="navbar-profile-button">
                {session.user.name}
              </Link>
            </>
          ) : (
            <form
              action={async () => {
                "use server";
                await signIn("github");
              }}
            >
              <button type="submit" className="navbar-login-button">
                Login
              </button>
            </form>
          )}
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
