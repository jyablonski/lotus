import { render, screen, fireEvent } from "@testing-library/react";
import { JournalTextEditor } from "@/components/journal/JournalTextEditor";

describe("JournalTextEditor", () => {
  const defaultProps = {
    value: "",
    onChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the label", () => {
    render(<JournalTextEditor {...defaultProps} />);
    expect(screen.getByText("Your Journal Entry")).toBeInTheDocument();
  });

  it("renders textarea with default placeholder", () => {
    render(<JournalTextEditor {...defaultProps} />);
    expect(
      screen.getByPlaceholderText(/What's on your mind today/),
    ).toBeInTheDocument();
  });

  it("renders textarea with custom placeholder", () => {
    render(<JournalTextEditor {...defaultProps} placeholder="Write here..." />);
    expect(screen.getByPlaceholderText("Write here...")).toBeInTheDocument();
  });

  it("displays the current value", () => {
    render(<JournalTextEditor {...defaultProps} value="Hello world" />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("Hello world");
  });

  it("calls onChange when typing", () => {
    const onChange = jest.fn();
    render(<JournalTextEditor {...defaultProps} onChange={onChange} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "New text" } });
    expect(onChange).toHaveBeenCalledWith("New text");
  });

  it("shows 0 words and 0 characters for empty value", () => {
    render(<JournalTextEditor {...defaultProps} value="" />);
    expect(screen.getByText(/0 words/)).toBeInTheDocument();
    expect(screen.getByText(/0 characters/)).toBeInTheDocument();
  });

  it("counts words correctly", () => {
    render(<JournalTextEditor {...defaultProps} value="Hello world today" />);
    expect(screen.getByText(/3 words/)).toBeInTheDocument();
  });

  it("counts characters correctly", () => {
    render(<JournalTextEditor {...defaultProps} value="Hello" />);
    expect(screen.getByText(/5 characters/)).toBeInTheDocument();
  });

  it("handles whitespace-only value as 0 words", () => {
    render(<JournalTextEditor {...defaultProps} value="   " />);
    expect(screen.getByText(/0 words/)).toBeInTheDocument();
  });
});
