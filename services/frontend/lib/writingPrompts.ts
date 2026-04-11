/** Curated journaling prompts — rotate or insert into the editor. */
export const WRITING_PROMPTS: readonly string[] = [
  "What felt meaningful today, even if it was small?",
  "What are you grateful for right now, and why?",
  "What challenged you recently, and what did you learn?",
  "Describe a moment you were proud of yourself this week.",
  "What would you tell a friend who felt the way you feel today?",
  "What do you need more of in your life? Less of?",
  "What are you looking forward to?",
  "What boundary do you want to honor more clearly?",
  "What habit would help you feel more grounded?",
  "If today were a chapter title, what would it be?",
];

export interface WritingPromptOption {
  promptId: string;
  promptText: string;
  inspirationTags: string[];
  tone: string;
  category: string;
  source: "static" | "community";
}

export function getStaticPromptOptions(): WritingPromptOption[] {
  return WRITING_PROMPTS.map((prompt, index) => ({
    promptId: `static-${index + 1}`,
    promptText: prompt,
    inspirationTags: [],
    tone: "gentle",
    category: "reflection",
    source: "static",
  }));
}

export function getPromptByIndex(index: number): string {
  return WRITING_PROMPTS[index % WRITING_PROMPTS.length] ?? WRITING_PROMPTS[0]!;
}
