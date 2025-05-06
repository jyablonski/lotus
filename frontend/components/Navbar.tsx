import Link from "next/link";
import Image from "next/image";
import React from "react";
import { auth } from "@/auth";
import { Login } from "@/components/auth/LoginButton";
import { Logout } from "@/components/auth/LogoutButton";
import UserAvatar from "@/components/UserAvatar";

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
              <Link href="/journal/create" className="navbar-link-button">
                Create
              </Link>

              <Logout />


              <Link href={`/about`} className="navbar-link-button">
                About
              </Link>

              <UserAvatar />
            </>
          ) : (
            <Login />
          )}
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
