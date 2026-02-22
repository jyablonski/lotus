import { render, screen } from "@testing-library/react";
import { SuccessMessage } from "@/components/journal/SuccessMessage";

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  CheckCircle: ({ className }: { className?: string }) => (
    <svg data-testid="check-circle-icon" className={className} />
  ),
}));

describe("SuccessMessage", () => {
  it("renders success heading", () => {
    render(<SuccessMessage />);
    expect(screen.getByText("Entry Saved Successfully!")).toBeInTheDocument();
  });

  it("renders redirect message", () => {
    render(<SuccessMessage />);
    expect(
      screen.getByText(/Redirecting you back to your journal/),
    ).toBeInTheDocument();
  });

  it("renders check circle icon", () => {
    render(<SuccessMessage />);
    expect(screen.getByTestId("check-circle-icon")).toBeInTheDocument();
  });
});
