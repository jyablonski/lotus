import { render, screen, fireEvent } from "@testing-library/react";
import { signOut } from "next-auth/react";
import { Logout } from "@/components/auth/LogoutButton";

jest.mock("lucide-react", () => ({
  LogOut: () => <svg data-testid="logout-icon" />,
}));

describe("Logout", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders 'Sign Out' button", () => {
    render(<Logout />);
    expect(
      screen.getByRole("button", { name: /Sign Out/ }),
    ).toBeInTheDocument();
  });

  it("renders logout icon", () => {
    render(<Logout />);
    expect(screen.getByTestId("logout-icon")).toBeInTheDocument();
  });

  it("calls signOut with callbackUrl on click", () => {
    render(<Logout />);
    fireEvent.click(screen.getByRole("button", { name: /Sign Out/ }));
    expect(signOut).toHaveBeenCalledWith({ callbackUrl: "/" });
  });
});
