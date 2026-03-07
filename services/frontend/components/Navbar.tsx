import Link from "next/link";
import React from "react";
import { auth } from "@/auth";
import { Login } from "@/components/auth/LoginButton";
import { NavLink } from "@/components/NavLink";
import UserAvatar from "@/components/UserAvatar";
import { ROUTES } from "@/lib/routes";

const Navbar = async () => {
  const session = await auth();

  return (
    <header className="border-b border-dark-600 shadow-lg backdrop-blur-sm bg-dark-800/90">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link
            href={ROUTES.home}
            className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
          >
            <span className="text-xl font-bold text-gradient">Lotus</span>
          </Link>

          {/* Navigation Links (logged in users) */}
          {session && session.user ? (
            <div className="flex items-center space-x-8">
              {/* Main Navigation */}
              <div className="hidden md:flex items-center space-x-6">
                <NavLink href={ROUTES.home}>Home</NavLink>
                <NavLink href={ROUTES.journal.home}>Journal</NavLink>
                <NavLink href={ROUTES.journal.calendar}>Calendar</NavLink>
                <NavLink href={ROUTES.profile}>Profile</NavLink>
              </div>

              {/* User Avatar */}
              <UserAvatar />
            </div>
          ) : (
            <Login />
          )}
        </div>

        {/* Mobile Navigation (logged in users) */}
        {session && session.user && (
          <div className="md:hidden border-t border-dark-700 pt-4 pb-3">
            <div className="flex space-x-6">
              <NavLink href={ROUTES.home}>Home</NavLink>
              <NavLink href={ROUTES.journal.home}>Journal</NavLink>
              <NavLink href={ROUTES.journal.calendar}>Calendar</NavLink>
              <NavLink href={ROUTES.profile}>Profile</NavLink>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Navbar;
