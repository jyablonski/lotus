"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { WRITING_PROMPTS, getPromptByIndex } from "@/lib/writingPrompts";

type WritingPromptBoxProps = {
  onInsert: (text: string) => void;
};

export function WritingPromptBox({ onInsert }: WritingPromptBoxProps) {
  const [index, setIndex] = useState(0);
  const prompt = getPromptByIndex(index);

  return (
    <div className="rounded-lg border border-lotus-500/25 bg-lotus-950/20 p-4 space-y-3">
      <div className="flex items-center gap-2 text-lotus-300 text-sm font-medium">
        <Sparkles size={16} className="shrink-0" aria-hidden />
        Need inspiration?
      </div>
      <p className="text-dark-200 text-sm leading-relaxed">
        &ldquo;{prompt}&rdquo;
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setIndex((i) => (i + 1) % WRITING_PROMPTS.length)}
          className="text-sm px-3 py-1.5 rounded-md border border-dark-600 text-dark-200 hover:bg-dark-700/50 transition-colors"
        >
          Another prompt
        </button>
        <button
          type="button"
          onClick={() => onInsert(prompt)}
          className="text-sm px-3 py-1.5 rounded-md bg-lotus-600/30 text-lotus-200 hover:bg-lotus-600/40 transition-colors"
        >
          Add to entry
        </button>
      </div>
    </div>
  );
}
