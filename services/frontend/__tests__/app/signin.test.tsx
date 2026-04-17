import { render, screen } from "@testing-library/react";
import SignInPage from "@/app/signin/page";

jest.mock("@/auth", () => ({
  auth: jest.fn().mockResolvedValue(null),
  signIn: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  redirect: jest.fn(),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  })),
  usePathname: jest.fn(() => "/signin"),
}));

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock("lucide-react", () => ({
  Heart: () => <svg data-testid="heart-icon" />,
  Github: () => <svg data-testid="github-icon" />,
  Mail: () => <svg data-testid="mail-icon" />,
}));

// SignInPage is an async server component, so we invoke it and render the resolved JSX.
async function renderSignInPage(searchParams = {}) {
  const jsx = await SignInPage({
    searchParams: Promise.resolve(searchParams),
  });
  return render(jsx);
}

describe("SignInPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders the 'Welcome to Lotus' heading", async () => {
    await renderSignInPage();
    expect(
      screen.getByRole("heading", { name: /welcome to lotus/i }),
    ).toBeInTheDocument();
  });

  test("renders email input field", async () => {
    await renderSignInPage();
    const emailInput = screen.getByLabelText(/email address/i);
    expect(emailInput).toBeInTheDocument();
    expect(emailInput).toHaveAttribute("type", "email");
    expect(emailInput).toHaveAttribute("name", "email");
    expect(emailInput).toBeRequired();
  });

  test("renders 'Sign in with Email' button", async () => {
    await renderSignInPage();
    expect(
      screen.getByRole("button", { name: /sign in with email/i }),
    ).toBeInTheDocument();
  });

  test("renders 'Sign in with GitHub' button", async () => {
    await renderSignInPage();
    expect(
      screen.getByRole("button", { name: /sign in with github/i }),
    ).toBeInTheDocument();
  });

  test("renders the 'or continue with' divider", async () => {
    await renderSignInPage();
    expect(screen.getByText(/or continue with/i)).toBeInTheDocument();
  });

  test("renders 'Back to home' link pointing to /", async () => {
    await renderSignInPage();
    const homeLink = screen.getByRole("link", { name: /back to home/i });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/");
  });

  test("shows generic error message for unknown errors", async () => {
    await renderSignInPage({ error: "SomeError" });
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  test("shows specific error for OAuthAccountNotLinked", async () => {
    await renderSignInPage({ error: "OAuthAccountNotLinked" });
    expect(
      screen.getByText(/already associated with another sign-in method/i),
    ).toBeInTheDocument();
  });

  test("does not show error message when no error param", async () => {
    await renderSignInPage();
    expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/already associated/i)).not.toBeInTheDocument();
  });

  test("redirects authenticated users to home", async () => {
    const { redirect } = require("next/navigation");
    const { auth } = require("@/auth");
    auth.mockResolvedValueOnce({
      user: { id: "123", email: "test@example.com" },
    });

    await renderSignInPage();
    expect(redirect).toHaveBeenCalledWith("/");
  });
});
