"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { TimezoneSelector } from "./TimezoneSelector";
import { CommunitySettingsCard } from "./CommunitySettingsCard";
import { ROUTES } from "@/lib/routes";

interface ProfileSettingsClientProps {
  timezone: string;
  communityInsightsOptIn: boolean;
  communityLocationOptIn: boolean;
  communityCountryCode: string;
  communityRegionCode: string;
}

export function ProfileSettingsClient({
  timezone,
  communityInsightsOptIn,
  communityLocationOptIn,
  communityCountryCode,
  communityRegionCode,
}: ProfileSettingsClientProps) {
  return (
    <div className="page-container">
      <div className="content-container space-y-8">
        <div>
          <Link
            href={ROUTES.profile}
            className="text-sm text-muted-dark hover:text-lotus-400 transition-colors"
          >
            ← Back to profile
          </Link>
        </div>

        <div>
          <h1 className="heading-1">Settings</h1>
          <p className="text-muted-dark mt-2">
            Manage your account and preferences.
          </p>
        </div>

        <Card>
          <CardContent className="p-6">
            <TimezoneSelector currentTimezone={timezone} />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <CommunitySettingsCard
              initialInsightsOptIn={communityInsightsOptIn}
              initialLocationOptIn={communityLocationOptIn}
              initialCountryCode={communityCountryCode}
              initialRegionCode={communityRegionCode}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
