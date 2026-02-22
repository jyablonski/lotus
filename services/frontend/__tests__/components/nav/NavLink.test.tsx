import { render, screen } from "@testing-library/react";
import { NavLink } from "@/components/NavLink";

jest.mock("next/link", () => {
  return ({
    children,
    href,
    className,
  }: {
    children: React.ReactNode;
    href: string;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  );
});

describe("NavLink", () => {
  it("renders children text", () => {
    render(<NavLink href="/test">Test Link</NavLink>);
    expect(screen.getByText("Test Link")).toBeInTheDocument();
  });

  it("renders as a link with correct href", () => {
    render(<NavLink href="/journal/home">Journal</NavLink>);
    const link = screen.getByRole("link", { name: "Journal" });
    expect(link).toHaveAttribute("href", "/journal/home");
  });

  it("applies base styling classes", () => {
    render(<NavLink href="/test">Test</NavLink>);
    const link = screen.getByRole("link");
    expect(link.className).toContain("text-sm");
    expect(link.className).toContain("font-medium");
  });

  it("applies additional className", () => {
    render(
      <NavLink href="/test" className="extra-class">
        Test
      </NavLink>,
    );
    const link = screen.getByRole("link");
    expect(link.className).toContain("extra-class");
  });
});
