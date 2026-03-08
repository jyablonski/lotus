"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { updateTimezone } from "@/actions/user";

const TIMEZONE_OPTIONS = [
  { value: "Pacific/Honolulu", label: "Hawaii (HST)" },
  { value: "America/Anchorage", label: "Alaska (AKST)" },
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/New_York", label: "Eastern Time (ET)" },
  { value: "America/Halifax", label: "Atlantic (AST)" },
  { value: "America/Sao_Paulo", label: "Brasilia (BRT)" },
  { value: "UTC", label: "UTC" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Paris", label: "Central Europe (CET)" },
  { value: "Europe/Helsinki", label: "Eastern Europe (EET)" },
  { value: "Europe/Moscow", label: "Moscow (MSK)" },
  { value: "Asia/Dubai", label: "Gulf (GST)" },
  { value: "Asia/Kolkata", label: "India (IST)" },
  { value: "Asia/Bangkok", label: "Indochina (ICT)" },
  { value: "Asia/Shanghai", label: "China (CST)" },
  { value: "Asia/Tokyo", label: "Japan (JST)" },
  { value: "Australia/Sydney", label: "Sydney (AEST)" },
  { value: "Pacific/Auckland", label: "New Zealand (NZST)" },
] as const;

interface TimezoneSelectorProps {
  currentTimezone: string;
}

export function TimezoneSelector({ currentTimezone }: TimezoneSelectorProps) {
  const { update: updateSession } = useSession();
  const [timezone, setTimezone] = useState(currentTimezone);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleTimezoneChange = useCallback(
    async (newTimezone: string) => {
      setTimezone(newTimezone);
      setSaving(true);
      setMessage(null);

      const result = await updateTimezone(newTimezone);

      if (result.success) {
        const newTz = result.timezone ?? newTimezone;
        await updateSession({ timezone: newTz });
        setMessage("Timezone updated.");
      } else {
        setMessage(result.error || "Failed to update timezone");
        setTimezone(currentTimezone);
      }
      setSaving(false);
    },
    [currentTimezone, updateSession],
  );

  // Auto-detect: if timezone is UTC, check if browser has a different one
  useEffect(() => {
    if (currentTimezone === "UTC") {
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (detected && detected !== "UTC") {
        handleTimezoneChange(detected);
      }
    }
  }, [currentTimezone, handleTimezoneChange]);

  return (
    <div className="space-y-2">
      <label
        htmlFor="timezone-select"
        className="text-sm font-medium text-dark-200"
      >
        Timezone
      </label>
      <select
        id="timezone-select"
        value={timezone}
        onChange={(e) => handleTimezoneChange(e.target.value)}
        disabled={saving}
        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-100 text-sm focus:outline-none focus:ring-2 focus:ring-lotus-500/50 focus:border-lotus-500/50 disabled:opacity-50"
      >
        {TIMEZONE_OPTIONS.map((tz) => (
          <option key={tz.value} value={tz.value}>
            {tz.label}
          </option>
        ))}
        {/* If user's timezone isn't in our list, still show it */}
        {!TIMEZONE_OPTIONS.some((tz) => tz.value === timezone) && (
          <option value={timezone}>{timezone}</option>
        )}
      </select>
      {saving && <p className="text-xs text-dark-400">Saving...</p>}
      {message && <p className="text-xs text-dark-400">{message}</p>}
    </div>
  );
}
