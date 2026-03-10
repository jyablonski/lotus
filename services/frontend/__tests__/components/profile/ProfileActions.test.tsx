import { render, screen } from "@testing-library/react";
import { ProfileActions } from "@/components/profile/ProfileActions";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock("lucide-react", () => ({
  PlusCircle: () => <svg data-testid="icon-plus" />,
  BarChart3: () => <svg data-testid="icon-chart" />,
  Calendar: () => <svg data-testid="icon-calendar" />,
  Settings: () => <svg data-testid="icon-settings" />,
  LogOut: () => <svg data-testid="icon-logout" />,
}));

jest.mock("@/components/auth/LogoutButton", () => ({
  Logout: () => <button data-testid="logout-button">Sign Out</button>,
}));

describe("ProfileActions", () => {
  it("renders 'Quick Actions' heading", () => {
    render(<ProfileActions />);
    expect(screen.getByText("Quick Actions")).toBeInTheDocument();
  });

  it("renders 'Create New Entry' link", () => {
    render(<ProfileActions />);
    const link = screen.getByText("Create New Entry").closest("a");
    expect(link).toHaveAttribute("href", "/journal/create");
  });

  it("renders 'View All Entries' link", () => {
    render(<ProfileActions />);
    const link = screen.getByText("View All Entries").closest("a");
    expect(link).toHaveAttribute("href", "/journal/home");
  });

  it("renders 'Calendar View' link", () => {
    render(<ProfileActions />);
    const link = screen.getByText("Calendar View").closest("a");
    expect(link).toHaveAttribute("href", "/journal/calendar");
  });

  it("renders 'Settings' link", () => {
    render(<ProfileActions />);
    const link = screen.getByText("Settings").closest("a");
    expect(link).toHaveAttribute("href", "/profile/settings");
  });

  it("renders Logout button", () => {
    render(<ProfileActions />);
    expect(screen.getByTestId("logout-button")).toBeInTheDocument();
  });
});
