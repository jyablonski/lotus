import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import { MaintenanceBanner } from "@/components/MaintenanceBanner";

describe("MaintenanceBanner", () => {
  it("renders maintenance message when not dismissed", () => {
    render(<MaintenanceBanner />);
    expect(screen.getByText(/Scheduled Maintenance/)).toBeInTheDocument();
    expect(
      screen.getByText(/We are performing maintenance/),
    ).toBeInTheDocument();
  });

  it("renders dismiss button with accessible label", () => {
    render(<MaintenanceBanner />);
    expect(
      screen.getByRole("button", { name: /Dismiss maintenance banner/ }),
    ).toBeInTheDocument();
  });

  it("hides banner when dismiss is clicked", () => {
    render(<MaintenanceBanner />);
    const dismiss = screen.getByRole("button", {
      name: /Dismiss maintenance banner/,
    });
    fireEvent.click(dismiss);
    expect(screen.queryByText(/Scheduled Maintenance/)).not.toBeInTheDocument();
  });
});
