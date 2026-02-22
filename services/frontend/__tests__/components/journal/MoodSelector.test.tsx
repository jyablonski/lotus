import { render, screen, fireEvent } from "@testing-library/react";
import { MoodSelector } from "@/components/journal/MoodSelector";

describe("MoodSelector", () => {
  const defaultProps = {
    selectedMood: "",
    onMoodChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders 'How are you feeling?' label", () => {
    render(<MoodSelector {...defaultProps} />);
    expect(screen.getByText("How are you feeling?")).toBeInTheDocument();
  });

  it("renders all 8 mood buttons", () => {
    render(<MoodSelector {...defaultProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(8);
  });

  it("renders mood labels", () => {
    render(<MoodSelector {...defaultProps} />);
    expect(screen.getByText("Excited")).toBeInTheDocument();
    expect(screen.getByText("Happy")).toBeInTheDocument();
    expect(screen.getByText("Content")).toBeInTheDocument();
    expect(screen.getByText("Neutral")).toBeInTheDocument();
    expect(screen.getByText("Tired")).toBeInTheDocument();
    expect(screen.getByText("Sad")).toBeInTheDocument();
    expect(screen.getByText("Anxious")).toBeInTheDocument();
    expect(screen.getByText("Angry")).toBeInTheDocument();
  });

  it("renders mood emojis", () => {
    render(<MoodSelector {...defaultProps} />);
    expect(screen.getByText("🤩")).toBeInTheDocument();
    expect(screen.getByText("😊")).toBeInTheDocument();
    expect(screen.getByText("😌")).toBeInTheDocument();
    expect(screen.getByText("😐")).toBeInTheDocument();
    expect(screen.getByText("😴")).toBeInTheDocument();
    expect(screen.getByText("😢")).toBeInTheDocument();
    expect(screen.getByText("😰")).toBeInTheDocument();
    expect(screen.getByText("😠")).toBeInTheDocument();
  });

  it("calls onMoodChange when a mood is clicked", () => {
    const onMoodChange = jest.fn();
    render(<MoodSelector {...defaultProps} onMoodChange={onMoodChange} />);
    fireEvent.click(screen.getByText("Happy"));
    expect(onMoodChange).toHaveBeenCalledWith("happy");
  });

  it("calls onMoodChange with correct key for each mood", () => {
    const onMoodChange = jest.fn();
    render(<MoodSelector {...defaultProps} onMoodChange={onMoodChange} />);

    fireEvent.click(screen.getByText("Excited"));
    expect(onMoodChange).toHaveBeenCalledWith("excited");

    fireEvent.click(screen.getByText("Angry"));
    expect(onMoodChange).toHaveBeenCalledWith("angry");
  });

  it("visually distinguishes the selected mood", () => {
    const { container } = render(
      <MoodSelector {...defaultProps} selectedMood="happy" />,
    );
    // The selected mood should have scale-105 class
    const buttons = container.querySelectorAll("button");
    const happyButton = Array.from(buttons).find((btn) =>
      btn.textContent?.includes("Happy"),
    );
    expect(happyButton?.className).toContain("scale-105");
  });

  it("does not apply selected styles to non-selected moods", () => {
    const { container } = render(
      <MoodSelector {...defaultProps} selectedMood="happy" />,
    );
    const buttons = container.querySelectorAll("button");
    const sadButton = Array.from(buttons).find((btn) =>
      btn.textContent?.includes("Sad"),
    );
    expect(sadButton?.className).not.toContain("scale-105");
  });
});
