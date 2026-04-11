import Link from "next/link";
import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { ROUTES } from "@/lib/routes";
import {
  formatCommunityScopeLabel,
  formatCommunityTimeRangeLabel,
} from "@/types/community";
import type { CommunityPromptSetData } from "@/types/community";

interface CommunityPromptsPanelProps {
  promptSet: CommunityPromptSetData | null;
  compact?: boolean;
}

export function CommunityPromptsPanel({
  promptSet,
  compact = false,
}: CommunityPromptsPanelProps) {
  const featuredPrompt = promptSet?.featuredPrompt ?? null;
  const alternatePrompts = promptSet?.alternatePrompts ?? [];
  const hasPrompts = Boolean(featuredPrompt);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-lotus-500/20 bg-lotus-950/20">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-lotus-300">
              <Sparkles size={16} aria-hidden />
              <span className="text-sm font-medium">Community prompts</span>
            </div>
            <h2 className="text-xl font-semibold text-primary-dark">
              Write with what the community is holding
            </h2>
          </div>
          {promptSet && !promptSet.isEmpty && (
            <span className="rounded-full border border-lotus-500/25 px-3 py-1 text-xs font-medium text-lotus-200">
              {formatCommunityScopeLabel(
                promptSet.appliedScopeType,
                promptSet.appliedScopeValue,
              )}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {hasPrompts ? (
          <>
            <div className="rounded-2xl border border-lotus-500/20 bg-gradient-to-br from-lotus-950/35 via-dark-800 to-dark-800 px-5 py-5">
              <p className="text-xs uppercase tracking-[0.24em] text-lotus-300">
                Featured prompt
              </p>
              <p className="mt-3 text-lg leading-relaxed text-primary-dark">
                &ldquo;{featuredPrompt?.promptText}&rdquo;
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {featuredPrompt?.inspirationTags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-lotus-500/10 px-3 py-1 text-xs font-medium text-lotus-200"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <p className="mt-4 text-sm text-muted-dark">
                {formatCommunityTimeRangeLabel(
                  promptSet?.timeRangeApplied ?? "",
                )}
                {" · "}
                {featuredPrompt?.category || "reflection"}
              </p>
            </div>

            {!compact && alternatePrompts.length > 0 && (
              <div className="space-y-3">
                <p className="text-sm font-medium text-secondary-dark">
                  Alternate ways in
                </p>
                <div className="grid gap-3">
                  {alternatePrompts.map((prompt) => (
                    <div
                      key={prompt.promptId}
                      className="rounded-xl border border-dark-600 bg-dark-800/60 px-4 py-3"
                    >
                      <p className="text-sm leading-relaxed text-primary-dark">
                        {prompt.promptText}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="rounded-xl border border-dashed border-dark-600 px-4 py-6 text-sm text-muted-dark">
            Community-informed prompts will show up here when a privacy-safe set
            is available. Until then, you can still start from a gentle writing
            prompt.
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          <Link href={ROUTES.journal.create} className="btn-primary">
            Start writing
          </Link>
          <Link href={ROUTES.community} className="btn-secondary">
            Explore community
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
