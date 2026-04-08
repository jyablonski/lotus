"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import {
  getStaticPromptOptions,
  type WritingPromptOption,
} from "@/lib/writingPrompts";
import type { CommunityPromptSetData } from "@/types/community";

type WritingPromptBoxProps = {
  onInsert: (text: string) => void;
  communityPromptSet?: CommunityPromptSetData | null;
};

function promptOptionsFromCommunity(
  communityPromptSet?: CommunityPromptSetData | null,
): WritingPromptOption[] {
  if (!communityPromptSet || communityPromptSet.isEmpty) {
    return getStaticPromptOptions();
  }

  const communityPrompts = [
    communityPromptSet.featuredPrompt,
    ...communityPromptSet.alternatePrompts,
  ]
    .filter(
      (
        prompt,
      ): prompt is NonNullable<typeof communityPromptSet.featuredPrompt> =>
        Boolean(prompt),
    )
    .map((prompt) => ({
      promptId: prompt.promptId,
      promptText: prompt.promptText,
      inspirationTags: prompt.inspirationTags,
      tone: prompt.tone,
      category: prompt.category,
      source: "community" as const,
    }));

  return communityPrompts.length > 0
    ? communityPrompts
    : getStaticPromptOptions();
}

export function WritingPromptBox({
  onInsert,
  communityPromptSet,
}: WritingPromptBoxProps) {
  const [index, setIndex] = useState(0);
  const prompts = promptOptionsFromCommunity(communityPromptSet);
  const prompt = prompts[index % prompts.length] ?? prompts[0];
  const isCommunityPrompt = prompt?.source === "community";
  const sourceLabel = isCommunityPrompt
    ? "Inspired by Community Pulse"
    : "A gentle starting point";

  return (
    <div className="rounded-lg border border-lotus-500/25 bg-lotus-950/20 p-4 space-y-3">
      <div className="flex items-center gap-2 text-lotus-300 text-sm font-medium">
        <Sparkles size={16} className="shrink-0" aria-hidden />
        Need inspiration?
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-lotus-500/20 bg-lotus-500/10 px-3 py-1 text-xs font-medium text-lotus-200">
          {sourceLabel}
        </span>
        {prompt?.inspirationTags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-dark-600 px-3 py-1 text-xs font-medium text-dark-200"
          >
            {tag}
          </span>
        ))}
      </div>
      <p className="text-dark-200 text-sm leading-relaxed">
        &ldquo;{prompt?.promptText}&rdquo;
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setIndex((i) => (i + 1) % prompts.length)}
          className="text-sm px-3 py-1.5 rounded-md border border-dark-600 text-dark-200 hover:bg-dark-700/50 transition-colors"
        >
          Another prompt
        </button>
        <button
          type="button"
          onClick={() => onInsert(prompt?.promptText ?? "")}
          className="text-sm px-3 py-1.5 rounded-md bg-lotus-600/30 text-lotus-200 hover:bg-lotus-600/40 transition-colors"
        >
          Add to entry
        </button>
      </div>
    </div>
  );
}
