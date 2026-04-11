"use client";

import { useState, useTransition } from "react";
import { updateCommunitySettings } from "@/actions/user";

interface CommunitySettingsCardProps {
  initialInsightsOptIn: boolean;
  initialLocationOptIn: boolean;
  initialCountryCode: string;
  initialRegionCode: string;
}

export function CommunitySettingsCard({
  initialInsightsOptIn,
  initialLocationOptIn,
  initialCountryCode,
  initialRegionCode,
}: CommunitySettingsCardProps) {
  const [communityInsightsOptIn, setCommunityInsightsOptIn] =
    useState(initialInsightsOptIn);
  const [communityLocationOptIn, setCommunityLocationOptIn] =
    useState(initialLocationOptIn);
  const [communityCountryCode, setCommunityCountryCode] =
    useState(initialCountryCode);
  const [communityRegionCode, setCommunityRegionCode] =
    useState(initialRegionCode);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const submit = () => {
    setMessage(null);

    startTransition(async () => {
      const result = await updateCommunitySettings({
        communityInsightsOptIn,
        communityLocationOptIn,
        communityCountryCode,
        communityRegionCode,
      });

      if (!result.success) {
        setMessage(result.error || "Failed to update community settings.");
        return;
      }

      setCommunityInsightsOptIn(result.communityInsightsOptIn ?? false);
      setCommunityLocationOptIn(result.communityLocationOptIn ?? false);
      setCommunityCountryCode(result.communityCountryCode ?? "");
      setCommunityRegionCode(result.communityRegionCode ?? "");
      setMessage("Community settings updated.");
    });
  };

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-primary-dark">
          Community participation
        </h2>
        <p className="text-sm leading-relaxed text-muted-dark">
          Opt in if you want your entries to contribute to anonymous,
          privacy-safe community trends. Raw journal text is never shown.
        </p>
      </div>

      <div className="rounded-2xl border border-dark-600 bg-dark-800/50 p-4 space-y-4">
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={communityInsightsOptIn}
            onChange={(e) => setCommunityInsightsOptIn(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-dark-500 bg-dark-700 text-lotus-500 focus:ring-lotus-500/40"
          />
          <span>
            <span className="block text-sm font-medium text-primary-dark">
              Share anonymous insight signals
            </span>
            <span className="block text-sm text-muted-dark">
              Contribute normalized themes and moods to aggregated community
              views.
            </span>
          </span>
        </label>

        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={communityLocationOptIn}
            onChange={(e) => setCommunityLocationOptIn(e.target.checked)}
            disabled={!communityInsightsOptIn}
            className="mt-1 h-4 w-4 rounded border-dark-500 bg-dark-700 text-lotus-500 focus:ring-lotus-500/40 disabled:opacity-50"
          />
          <span>
            <span className="block text-sm font-medium text-primary-dark">
              Allow coarse nearby context
            </span>
            <span className="block text-sm text-muted-dark">
              Use broad country and region codes only, so the app can fall back
              between nearby and global views safely.
            </span>
          </span>
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label
              htmlFor="community-country-code"
              className="text-sm font-medium text-dark-200"
            >
              Country code
            </label>
            <input
              id="community-country-code"
              type="text"
              value={communityCountryCode}
              onChange={(e) => setCommunityCountryCode(e.target.value)}
              maxLength={2}
              placeholder="US"
              disabled={!communityInsightsOptIn || !communityLocationOptIn}
              className="input-primary disabled:opacity-50"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="community-region-code"
              className="text-sm font-medium text-dark-200"
            >
              Region code
            </label>
            <input
              id="community-region-code"
              type="text"
              value={communityRegionCode}
              onChange={(e) => setCommunityRegionCode(e.target.value)}
              maxLength={12}
              placeholder="US-CA"
              disabled={!communityInsightsOptIn || !communityLocationOptIn}
              className="input-primary disabled:opacity-50"
            />
          </div>
        </div>

        <div className="rounded-xl border border-dashed border-dark-600 px-4 py-3 text-sm leading-relaxed text-muted-dark">
          Nearby views only appear when there is a large enough local cohort.
          Otherwise the app automatically falls back to a broader global view.
        </div>

        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={submit}
            disabled={isPending}
            className="btn-primary disabled:opacity-60"
          >
            {isPending ? "Saving..." : "Save community settings"}
          </button>
          {message && <p className="text-sm text-muted-dark">{message}</p>}
        </div>
      </div>
    </div>
  );
}
