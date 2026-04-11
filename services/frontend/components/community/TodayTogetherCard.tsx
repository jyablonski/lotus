import Link from "next/link";
import { ArrowRight, BookOpenText, Compass, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { ROUTES } from "@/lib/routes";
import {
  formatCommunityDateLabel,
  formatCommunityScopeLabel,
  isCommunityFallback,
} from "@/types/community";
import type { TodayTogetherData } from "@/types/community";

interface TodayTogetherCardProps {
  snapshot: TodayTogetherData | null;
}

export function TodayTogetherCard({ snapshot }: TodayTogetherCardProps) {
  const isEmpty = !snapshot || snapshot.isEmpty;
  const isFallback = isCommunityFallback(snapshot?.privacy);
  const themes = snapshot?.themes.slice(0, 3) ?? [];

  return (
    <Card className="overflow-hidden border-lotus-500/25">
      <CardHeader className="border-b border-lotus-500/15 bg-gradient-to-r from-lotus-950/30 via-dark-800 to-dark-800">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-lotus-300">
              <Compass size={16} aria-hidden />
              <span className="text-sm font-medium">Today, Together</span>
            </div>
            <h2 className="text-2xl font-semibold text-primary-dark">
              A calm snapshot of what the community is feeling
            </h2>
          </div>
          <div className="rounded-full border border-lotus-500/25 px-3 py-1 text-xs font-medium text-lotus-200">
            {snapshot
              ? formatCommunityScopeLabel(
                  snapshot.appliedScopeType,
                  snapshot.appliedScopeValue,
                )
              : "Community overview"}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-dark-400">
              {snapshot
                ? formatCommunityDateLabel(snapshot.bucketDate)
                : "Today"}
            </p>
            <p className="mt-2 max-w-3xl text-lg leading-relaxed text-primary-dark">
              {isEmpty
                ? "The community view is quiet right now. You can still begin with a gentle prompt and let your own page lead."
                : snapshot.communityNote}
            </p>
          </div>
          {isFallback && (
            <div className="rounded-full bg-dark-800 px-3 py-1 text-xs font-medium text-dark-200">
              Using a broader privacy-safe view
            </div>
          )}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-2xl border border-dark-600 bg-dark-800/55 p-4">
            <p className="text-sm font-medium text-secondary-dark">
              Themes showing up most
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {themes.length > 0 ? (
                themes.map((theme) => (
                  <span
                    key={theme.name}
                    className="rounded-full border border-lotus-500/20 bg-lotus-500/10 px-3 py-1.5 text-sm font-medium text-lotus-100"
                  >
                    {theme.name}
                  </span>
                ))
              ) : (
                <span className="text-sm text-muted-dark">
                  Reflection, rest, and change prompts will appear here when a
                  safe cohort is available.
                </span>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-dark-600 bg-dark-800/55 p-4">
            <p className="text-sm font-medium text-secondary-dark">
              Dominant mood
            </p>
            <p className="mt-3 text-2xl font-semibold capitalize text-primary-dark">
              {snapshot?.dominantMood || "Grounded"}
            </p>
            <p className="mt-2 text-sm text-muted-dark">
              Broad signals only, never individual entries.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link href={ROUTES.journal.create} className="btn-primary">
            <span className="inline-flex items-center gap-2">
              <BookOpenText size={16} aria-hidden />
              Start writing
            </span>
          </Link>
          <Link href={ROUTES.community} className="btn-secondary">
            <span className="inline-flex items-center gap-2">
              Explore Community Pulse
              <ArrowRight size={16} aria-hidden />
            </span>
          </Link>
          <Link href={ROUTES.journal.create} className="btn-ghost">
            <span className="inline-flex items-center gap-2">
              <Sparkles size={16} aria-hidden />
              Start with a prompt
            </span>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
