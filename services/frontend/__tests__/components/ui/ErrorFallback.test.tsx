import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorFallback } from "@/components/ui/ErrorFallback";
import { trackEvent } from "@/lib/analytics";

jest.mock("next/navigation", () => ({
  usePathname: () => "/journal/home",
}));
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});
jest.mock("@/lib/analytics", () => ({
  trackEvent: jest.fn(),
}));

const mockReset = jest.fn();
const mockError = new Error("Test error");

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("ErrorFallback", () => {
  it("renders message and Try again button", () => {
    render(
      <ErrorFallback
        error={mockError}
        reset={mockReset}
        logLabel="Test"
        message="Something failed."
      />,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Something failed.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Try again/ }),
    ).toBeInTheDocument();
  });

  it("calls reset when Try again is clicked", () => {
    render(
      <ErrorFallback
        error={mockError}
        reset={mockReset}
        logLabel="Test"
        message="Something failed."
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Try again/ }));
    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it("calls trackEvent with error_encountered", () => {
    render(
      <ErrorFallback
        error={mockError}
        reset={mockReset}
        logLabel="Test"
        message="Something failed."
      />,
    );
    expect(trackEvent).toHaveBeenCalledWith("error_encountered", {
      error_type: "load_failed",
      page: "/journal/home",
    });
  });

  it("renders back link when backHref is provided", () => {
    render(
      <ErrorFallback
        error={mockError}
        reset={mockReset}
        logLabel="Test"
        message="Something failed."
        backHref="/dashboard"
        backLabel="Go to Dashboard"
      />,
    );
    const backLink = screen.getByRole("link", { name: /Go to Dashboard/ });
    expect(backLink).toBeInTheDocument();
    expect(backLink).toHaveAttribute("href", "/dashboard");
  });

  it("uses default back label when backLabel not provided", () => {
    render(
      <ErrorFallback
        error={mockError}
        reset={mockReset}
        logLabel="Test"
        message="Something failed."
        backHref="/"
      />,
    );
    expect(
      screen.getByRole("link", { name: /Go to Dashboard/ }),
    ).toBeInTheDocument();
  });

  it("does not render back link when backHref is omitted", () => {
    render(
      <ErrorFallback
        error={mockError}
        reset={mockReset}
        logLabel="Test"
        message="Something failed."
      />,
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
