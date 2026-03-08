import { render, screen, fireEvent } from "@testing-library/react";
import { CreateJournalForm } from "@/components/journal/CreateJournalForm";

// Mock child components since they're tested separately
jest.mock("@/components/journal/MoodSelector", () => ({
  MoodSlider: ({
    value,
    onValueChange,
  }: {
    value: number;
    onValueChange: (value: number) => void;
  }) => (
    <div data-testid="mood-slider">
      <span data-testid="mood-value">{value}</span>
      <button type="button" onClick={() => onValueChange(7)}>
        Set 7
      </button>
    </div>
  ),
}));

jest.mock("@/components/journal/JournalTextEditor", () => ({
  JournalTextEditor: ({
    value,
    onChange,
  }: {
    value: string;
    onChange: (value: string) => void;
  }) => (
    <div data-testid="text-editor">
      <textarea
        data-testid="mock-textarea"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  ),
}));

describe("CreateJournalForm", () => {
  const defaultProps = {
    entry: "",
    setEntry: jest.fn(),
    mood: 5,
    setMood: jest.fn(),
    onSubmit: jest.fn(),
    isSubmitting: false,
    error: null,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders MoodSlider", () => {
    render(<CreateJournalForm {...defaultProps} />);
    expect(screen.getByTestId("mood-slider")).toBeInTheDocument();
  });

  it("renders JournalTextEditor", () => {
    render(<CreateJournalForm {...defaultProps} />);
    expect(screen.getByTestId("text-editor")).toBeInTheDocument();
  });

  it("renders Save Entry button", () => {
    render(<CreateJournalForm {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Save Entry" }),
    ).toBeInTheDocument();
  });

  it("renders Clear button", () => {
    render(<CreateJournalForm {...defaultProps} />);
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
  });

  describe("submit button disabled states", () => {
    it("is disabled when entry is empty", () => {
      render(<CreateJournalForm {...defaultProps} entry="" />);
      expect(screen.getByRole("button", { name: "Save Entry" })).toBeDisabled();
    });

    it("is disabled when isSubmitting", () => {
      render(
        <CreateJournalForm
          {...defaultProps}
          entry="Some text"
          mood={7}
          isSubmitting={true}
        />,
      );
      expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
    });

    it("is enabled when entry is provided", () => {
      render(
        <CreateJournalForm {...defaultProps} entry="Some text" mood={7} />,
      );
      expect(
        screen.getByRole("button", { name: "Save Entry" }),
      ).not.toBeDisabled();
    });

    it("is disabled when entry is whitespace only", () => {
      render(<CreateJournalForm {...defaultProps} entry="   " mood={7} />);
      expect(screen.getByRole("button", { name: "Save Entry" })).toBeDisabled();
    });
  });

  it("shows 'Saving...' text when isSubmitting", () => {
    render(
      <CreateJournalForm
        {...defaultProps}
        entry="text"
        mood={7}
        isSubmitting={true}
      />,
    );
    expect(screen.getByText("Saving...")).toBeInTheDocument();
  });

  it("shows error message when error prop is set", () => {
    render(
      <CreateJournalForm {...defaultProps} error="Something went wrong" />,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("does not show error when error is null", () => {
    const { container } = render(
      <CreateJournalForm {...defaultProps} error={null} />,
    );
    expect(container.querySelector(".alert-error")).not.toBeInTheDocument();
  });

  it("calls onSubmit when form is submitted", () => {
    const onSubmit = jest.fn((e) => e.preventDefault());
    render(
      <CreateJournalForm
        {...defaultProps}
        entry="Some text"
        mood={7}
        onSubmit={onSubmit}
      />,
    );
    fireEvent.submit(screen.getByRole("button", { name: "Save Entry" }));
    expect(onSubmit).toHaveBeenCalled();
  });

  it("calls setEntry and setMood(5) on Clear", () => {
    const setEntry = jest.fn();
    const setMood = jest.fn();
    render(
      <CreateJournalForm
        {...defaultProps}
        entry="text"
        mood={7}
        setEntry={setEntry}
        setMood={setMood}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(setEntry).toHaveBeenCalledWith("");
    expect(setMood).toHaveBeenCalledWith(5);
  });
});
