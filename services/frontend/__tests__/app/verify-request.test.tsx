import { render, screen } from "@testing-library/react";
import VerifyRequestPage from "@/app/verify-request/page";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock("lucide-react", () => ({
  Heart: () => <svg data-testid="heart-icon" />,
  Mail: () => <svg data-testid="mail-icon" />,
}));

describe("VerifyRequestPage", () => {
  test("renders 'Check your email' heading", () => {
    render(<VerifyRequestPage />);
    expect(
      screen.getByRole("heading", { name: /check your email/i }),
    ).toBeInTheDocument();
  });

  test("shows instruction text about the sign-in link", () => {
    render(<VerifyRequestPage />);
    expect(screen.getByText(/we sent you a sign-in link/i)).toBeInTheDocument();
  });

  test("shows expiration notice", () => {
    render(<VerifyRequestPage />);
    expect(
      screen.getByText(/the link will expire in 24 hours/i),
    ).toBeInTheDocument();
  });

  test("has a 'Try again' link pointing to /signin", () => {
    render(<VerifyRequestPage />);
    const tryAgainLink = screen.getByRole("link", { name: /try again/i });
    expect(tryAgainLink).toBeInTheDocument();
    expect(tryAgainLink).toHaveAttribute("href", "/signin");
  });

  test("has a 'Back to home' link pointing to /", () => {
    render(<VerifyRequestPage />);
    const homeLink = screen.getByRole("link", { name: /back to home/i });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/");
  });

  test("renders the mail icon", () => {
    render(<VerifyRequestPage />);
    expect(screen.getByTestId("mail-icon")).toBeInTheDocument();
  });
});
