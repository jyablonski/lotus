import { render, screen, fireEvent } from "@testing-library/react";
import { CreateJournalForm } from "@/components/journal/CreateJournalForm";

// Mock child components since they're tested separately
jest.mock("@/components/journal/MoodSelector", () => ({
  MoodSelector: ({
    selectedMood,
    onMoodChange,
  }: {
    selectedMood: string;
    onMoodChange: (mood: string) => void;
  }) => (
    <div data-testid="mood-selector">
      <span data-testid="selected-mood">{selectedMood}</span>
      <button type="button" onClick={() => onMoodChange("happy")}>
        Select Happy
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
    mood: "",
    setMood: jest.fn(),
    onSubmit: jest.fn(),
    isSubmitting: false,
    error: null,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders MoodSelector", () => {
    render(<CreateJournalForm {...defaultProps} />);
    expect(screen.getByTestId("mood-selector")).toBeInTheDocument();
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
      render(<CreateJournalForm {...defaultProps} entry="" mood="happy" />);
      expect(screen.getByRole("button", { name: "Save Entry" })).toBeDisabled();
    });

    it("is disabled when mood is empty", () => {
      render(<CreateJournalForm {...defaultProps} entry="Some text" mood="" />);
      expect(screen.getByRole("button", { name: "Save Entry" })).toBeDisabled();
    });

    it("is disabled when isSubmitting", () => {
      render(
        <CreateJournalForm
          {...defaultProps}
          entry="Some text"
          mood="happy"
          isSubmitting={true}
        />,
      );
      expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
    });

    it("is enabled when entry and mood are provided", () => {
      render(
        <CreateJournalForm {...defaultProps} entry="Some text" mood="happy" />,
      );
      expect(
        screen.getByRole("button", { name: "Save Entry" }),
      ).not.toBeDisabled();
    });

    it("is disabled when entry is whitespace only", () => {
      render(<CreateJournalForm {...defaultProps} entry="   " mood="happy" />);
      expect(screen.getByRole("button", { name: "Save Entry" })).toBeDisabled();
    });
  });

  it("shows 'Saving...' text when isSubmitting", () => {
    render(
      <CreateJournalForm
        {...defaultProps}
        entry="text"
        mood="happy"
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
        mood="happy"
        onSubmit={onSubmit}
      />,
    );
    fireEvent.submit(screen.getByRole("button", { name: "Save Entry" }));
    expect(onSubmit).toHaveBeenCalled();
  });

  it("calls setEntry and setMood with empty values on Clear", () => {
    const setEntry = jest.fn();
    const setMood = jest.fn();
    render(
      <CreateJournalForm
        {...defaultProps}
        entry="text"
        mood="happy"
        setEntry={setEntry}
        setMood={setMood}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(setEntry).toHaveBeenCalledWith("");
    expect(setMood).toHaveBeenCalledWith("");
  });
});
