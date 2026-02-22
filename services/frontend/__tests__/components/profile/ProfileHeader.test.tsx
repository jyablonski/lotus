import { render, screen, act } from "@testing-library/react";
import { ProfileHeader } from "@/components/profile/ProfileHeader";

jest.mock("lucide-react", () => ({
  User: () => <svg data-testid="user-icon" />,
}));

jest.mock("next/image", () => {
  return ({ src, alt, ...props }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} {...props} />
  );
});

describe("ProfileHeader", () => {
  const defaultProps = {
    name: "Jane Doe",
    email: "jane@example.com",
    image: "https://example.com/avatar.jpg",
    signupDate: "2025-01-15T12:00:00Z",
    firstEntryDate: null as Date | null,
  };

  it("renders the user name", () => {
    render(<ProfileHeader {...defaultProps} />);
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
  });

  it("renders the user email", () => {
    render(<ProfileHeader {...defaultProps} />);
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
  });

  it("renders avatar image when provided", () => {
    render(<ProfileHeader {...defaultProps} />);
    const img = screen.getByAltText("Jane Doe's avatar");
    expect(img).toHaveAttribute("src", "https://example.com/avatar.jpg");
  });

  it("renders user icon fallback when no image", () => {
    render(<ProfileHeader {...defaultProps} image={null} />);
    expect(screen.getByTestId("user-icon")).toBeInTheDocument();
  });

  it("renders formatted signup date", () => {
    render(<ProfileHeader {...defaultProps} />);
    expect(screen.getByText("Member since:")).toBeInTheDocument();
    expect(screen.getByText("January 15, 2025")).toBeInTheDocument();
  });

  it("calculates and shows days since signup after hydration", async () => {
    await act(async () => {
      render(<ProfileHeader {...defaultProps} />);
    });
    // After useEffect, should show "X days ago"
    expect(screen.getByText(/days ago/)).toBeInTheDocument();
  });

  it("renders first entry date when provided", () => {
    render(
      <ProfileHeader
        {...defaultProps}
        firstEntryDate={new Date(2025, 1, 20)} // Feb 20, 2025
      />,
    );
    expect(screen.getByText("First journal entry:")).toBeInTheDocument();
    expect(screen.getByText("February 20, 2025")).toBeInTheDocument();
  });

  it("does not show first entry section when null", () => {
    render(<ProfileHeader {...defaultProps} firstEntryDate={null} />);
    expect(screen.queryByText("First journal entry:")).not.toBeInTheDocument();
  });
});
