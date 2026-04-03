import { render, screen } from "@testing-library/react";
import Navbar from "@/components/Navbar";

// Mock auth
jest.mock("@/auth", () => ({
  auth: jest.fn(),
}));

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock("@/components/auth/LoginButton", () => ({
  Login: () => <button data-testid="login-button">Login</button>,
}));

jest.mock("@/components/NavLink", () => ({
  NavLink: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => (
    <a href={href} data-testid="nav-link">
      {children}
    </a>
  ),
}));

jest.mock("@/components/UserAvatar", () => {
  return () => <div data-testid="user-avatar">Avatar</div>;
});

import { auth } from "@/auth";
const mockAuth = auth as jest.Mock;

describe("Navbar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("when user is not authenticated", () => {
    beforeEach(() => {
      mockAuth.mockResolvedValue(null);
    });

    it("renders the Lotus logo link", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      const logo = screen.getByText("Lotus");
      expect(logo.closest("a")).toHaveAttribute("href", "/");
    });

    it("shows login button", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      expect(screen.getByTestId("login-button")).toBeInTheDocument();
    });

    it("does not show navigation links", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      expect(screen.queryByText("Journal")).not.toBeInTheDocument();
      expect(screen.queryByText("Calendar")).not.toBeInTheDocument();
    });

    it("does not show user avatar", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      expect(screen.queryByTestId("user-avatar")).not.toBeInTheDocument();
    });
  });

  describe("when user is authenticated", () => {
    beforeEach(() => {
      mockAuth.mockResolvedValue({
        user: {
          name: "Jane",
          email: "jane@example.com",
          image: "https://example.com/avatar.jpg",
        },
        expires: "2099-01-01",
      });
    });

    it("shows navigation links", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      expect(screen.getAllByText("Home")).toHaveLength(2); // desktop + mobile
      expect(screen.getAllByText("Journal")).toHaveLength(2);
      expect(screen.getAllByText("Calendar")).toHaveLength(2);
      expect(screen.getAllByText("Profile")).toHaveLength(2);
    });

    it("shows user avatar", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
    });

    it("does not show login button", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      expect(screen.queryByTestId("login-button")).not.toBeInTheDocument();
    });

    it("renders mobile navigation", async () => {
      const NavbarEl = await Navbar();
      render(NavbarEl);
      // Mobile nav has duplicate links
      const homeLinks = screen.getAllByText("Home");
      expect(homeLinks).toHaveLength(2);
    });
  });
});
