import { fireEvent, render, screen } from "@testing-library/react";
import { WritingPromptBox } from "@/components/journal/WritingPromptBox";

describe("WritingPromptBox", () => {
  it("uses community prompts when they are available", () => {
    const onInsert = jest.fn();

    render(
      <WritingPromptBox
        onInsert={onInsert}
        communityPromptSet={{
          featuredPrompt: {
            promptId: "community-1",
            promptText: "What part of you needs a little gentleness today?",
            inspirationTags: ["rest", "care"],
            tone: "gentle",
            timeRangeApplied: "today",
            scopeApplied: "global",
            generationMethod: "template",
            category: "grounding",
          },
          alternatePrompts: [],
          timeRangeApplied: "today",
          appliedScopeType: "global",
          appliedScopeValue: "global",
          privacy: {
            state: "ready",
            scopeFallbackApplied: false,
            periodFallbackApplied: false,
          },
          generatedAt: "2026-04-07T10:00:00Z",
          isEmpty: false,
        }}
      />,
    );

    expect(screen.getByText("Inspired by Community Pulse")).toBeInTheDocument();
    expect(
      screen.getByText(/What part of you needs a little gentleness today/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Add to entry" }));
    expect(onInsert).toHaveBeenCalledWith(
      "What part of you needs a little gentleness today?",
    );
  });

  it("falls back to static prompts when community data is unavailable", () => {
    render(<WritingPromptBox onInsert={jest.fn()} communityPromptSet={null} />);

    expect(screen.getByText("A gentle starting point")).toBeInTheDocument();
    expect(
      screen.getByText(/What felt meaningful today, even if it was small/i),
    ).toBeInTheDocument();
  });
});
