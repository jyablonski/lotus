import { render, screen, fireEvent } from "@testing-library/react";
import { MoodSlider } from "@/components/journal/MoodSelector";

describe("MoodSlider", () => {
  it("renders label and value", () => {
    render(<MoodSlider value={5} onValueChange={jest.fn()} />);
    expect(
      screen.getByText(/How are you feeling\? \(1-10\)/),
    ).toBeInTheDocument();
    expect(screen.getByText("Mood: 5")).toBeInTheDocument();
  });

  it("renders range input with min/max", () => {
    render(<MoodSlider value={5} onValueChange={jest.fn()} />);
    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("min", "1");
    expect(slider).toHaveAttribute("max", "10");
    expect(slider).toHaveValue("5");
  });

  it("calls onValueChange when slider changes", () => {
    const onValueChange = jest.fn();
    render(<MoodSlider value={5} onValueChange={onValueChange} />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "7" } });
    expect(onValueChange).toHaveBeenCalledWith(7);
  });

  it("respects custom min/max", () => {
    render(<MoodSlider value={3} onValueChange={jest.fn()} min={1} max={5} />);
    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("min", "1");
    expect(slider).toHaveAttribute("max", "5");
    expect(screen.getByText("Mood: 3")).toBeInTheDocument();
  });
});
