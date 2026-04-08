import Link from "next/link";
import { ShieldCheck, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { ROUTES } from "@/lib/routes";
import {
  COMMUNITY_SCOPE_OPTIONS,
  COMMUNITY_TIME_RANGE_OPTIONS,
  formatCommunityScopeLabel,
  formatCommunityTimeRangeLabel,
  isCommunityFallback,
} from "@/types/community";
import type {
  CommunityPromptSetData,
  CommunityPulseData,
  CommunityScopePreference,
  CommunityTimeRange,
} from "@/types/community";
import { CommunityMetricList } from "./CommunityMetricList";
import { CommunityPromptsPanel } from "./CommunityPromptsPanel";

interface CommunityPulsePageProps {
  pulse: CommunityPulseData | null;
  promptSet: CommunityPromptSetData | null;
  selectedTimeRange: CommunityTimeRange;
  selectedScope: CommunityScopePreference;
  isCommunityOptedIn?: boolean;
}

function communityHref(
  timeRange: CommunityTimeRange,
  scope: CommunityScopePreference,
): string {
  const params = new URLSearchParams({
    timeRange,
    scope,
  });

  return `${ROUTES.community}?${params.toString()}`;
}

export function CommunityPulsePage({
  pulse,
  promptSet,
  selectedTimeRange,
  selectedScope,
  isCommunityOptedIn = false,
}: CommunityPulsePageProps) {
  const isEmpty = !pulse || pulse.isEmpty;
  const scopeLabel = pulse
    ? formatCommunityScopeLabel(pulse.appliedScopeType, pulse.appliedScopeValue)
    : selectedScope === "nearby"
      ? "Nearby community"
      : "Global community";
  const timeLabel = formatCommunityTimeRangeLabel(
    pulse?.appliedTimeRange || selectedTimeRange,
  );

  return (
    <div className="page-container">
      <div className="content-container space-y-8">
        <Card className="overflow-hidden border-lotus-500/25">
          <CardContent className="bg-gradient-to-br from-lotus-950/35 via-dark-800 to-dark-900 px-6 py-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full border border-lotus-500/20 bg-lotus-500/10 px-3 py-1 text-sm font-medium text-lotus-200">
                  <ShieldCheck size={16} aria-hidden />
                  Anonymous, opt-in community trends
                </div>
                <div className="space-y-3">
                  <h1 className="heading-1 max-w-3xl">Community Pulse</h1>
                  <p className="max-w-2xl text-base leading-relaxed text-secondary-dark">
                    A privacy-forward look at what people are broadly writing
                    about right now. No quotes, no individual entries, just
                    shared signals you can gently reflect with.
                  </p>
                </div>
              </div>
              <div className="rounded-2xl border border-lotus-500/15 bg-dark-900/60 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.24em] text-dark-400">
                  Current view
                </p>
                <p className="mt-2 text-lg font-semibold text-primary-dark">
                  {timeLabel}
                </p>
                <p className="text-sm text-muted-dark">{scopeLabel}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-primary-dark">
                Time range
              </h2>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              {COMMUNITY_TIME_RANGE_OPTIONS.map((option) => {
                const active = option.value === selectedTimeRange;

                return (
                  <Link
                    key={option.value}
                    href={communityHref(option.value, selectedScope)}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                      active
                        ? "bg-lotus-500/15 text-lotus-100 border border-lotus-500/30"
                        : "bg-dark-800 text-dark-200 border border-dark-600 hover:border-lotus-500/25 hover:text-primary-dark"
                    }`}
                  >
                    {option.label}
                  </Link>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-primary-dark">Scope</h2>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              {COMMUNITY_SCOPE_OPTIONS.map((option) => {
                const active = option.value === selectedScope;

                return (
                  <Link
                    key={option.value}
                    href={communityHref(selectedTimeRange, option.value)}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                      active
                        ? "bg-lotus-500/15 text-lotus-100 border border-lotus-500/30"
                        : "bg-dark-800 text-dark-200 border border-dark-600 hover:border-lotus-500/25 hover:text-primary-dark"
                    }`}
                  >
                    {option.label}
                  </Link>
                );
              })}
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-8 xl:grid-cols-[1.35fr_0.95fr]">
          <div className="space-y-8">
            {!isCommunityOptedIn && (
              <Card className="border-lotus-500/25">
                <CardContent className="space-y-4 p-6">
                  <div className="space-y-2">
                    <h2 className="text-xl font-semibold text-primary-dark">
                      Want to help shape Community Pulse?
                    </h2>
                    <p className="text-sm leading-relaxed text-muted-dark">
                      You can opt in from settings if you want your entries to
                      contribute anonymous, privacy-safe themes and moods to
                      these shared views.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Link href={ROUTES.profileSettings} className="btn-primary">
                      Review community settings
                    </Link>
                    <Link
                      href={ROUTES.journal.create}
                      className="btn-secondary"
                    >
                      Keep journaling privately
                    </Link>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="border-lotus-500/20">
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-semibold text-primary-dark">
                      Community note
                    </h2>
                    <p className="mt-1 text-sm text-muted-dark">
                      A short, aggregated read on the current moment.
                    </p>
                  </div>
                  {pulse && isCommunityFallback(pulse.privacy) && (
                    <span className="rounded-full bg-dark-800 px-3 py-1 text-xs font-medium text-dark-200">
                      Broader fallback applied
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-lg leading-relaxed text-primary-dark">
                  {isEmpty
                    ? "Community Pulse is still warming up for this view. When a privacy-safe cohort is available, you’ll see shared themes, mood patterns, and a short note here."
                    : pulse.communitySummary}
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link href={ROUTES.journal.create} className="btn-primary">
                    Start writing
                  </Link>
                  <Link href={ROUTES.journal.create} className="btn-secondary">
                    Use a prompt
                  </Link>
                </div>
              </CardContent>
            </Card>

            <CommunityMetricList
              title="Top themes"
              description="The broad topics showing up most often in this view."
              metrics={pulse?.topThemes ?? []}
              emptyMessage="Themes will appear here once enough opt-in, analyzed entries are available."
            />

            <CommunityMetricList
              title="Rising themes"
              description="Themes gaining momentum compared with the previous window."
              metrics={pulse?.risingThemes ?? []}
              emptyMessage="Rising trends show up once there is enough comparison data to do that safely."
            />
          </div>

          <div className="space-y-8">
            <CommunityMetricList
              title="Top moods"
              description="Broad emotional tones, never individual feelings attributed to a person."
              metrics={pulse?.topMoods ?? []}
              emptyMessage="Mood trends will show up here once enough shared data is available."
            />

            <CommunityPromptsPanel promptSet={promptSet} />

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sparkles size={18} className="text-lotus-300" aria-hidden />
                  <h2 className="text-xl font-semibold text-primary-dark">
                    Privacy first
                  </h2>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-sm leading-relaxed text-muted-dark">
                <p>
                  Community surfaces only use anonymous, opt-in aggregate data.
                  Raw journal text and exact locations never appear here.
                </p>
                <p>
                  If a nearby group is too small, this page quietly falls back
                  to a broader view instead of showing a narrow cohort.
                </p>
                <p>
                  The goal is resonance, not surveillance. This is meant to help
                  you feel less alone, then turn back toward your own page.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
