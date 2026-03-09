import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { Login } from "@/components/auth/LoginButton";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe("Login", () => {
  it("renders a link with 'Login' text", () => {
    render(<Login />);
    expect(screen.getByRole("link", { name: /Login/ })).toBeInTheDocument();
  });

  it("links to signin route", () => {
    render(<Login />);
    const link = screen.getByRole("link", { name: /Login/ });
    expect(link).toHaveAttribute("href", "/signin");
  });
});
