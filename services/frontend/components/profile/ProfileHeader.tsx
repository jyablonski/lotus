"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { User } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";

interface ProfileHeaderProps {
  name: string;
  email: string;
  image: string | null;
  signupDate: string;
  firstEntryDate: Date | null;
}

/**
 * Format date in a locale-independent way to avoid hydration mismatch.
 */
function formatDate(date: Date): string {
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

export function ProfileHeader({
  name,
  email,
  image,
  signupDate,
  firstEntryDate,
}: ProfileHeaderProps) {
  const formattedSignupDate = formatDate(new Date(signupDate));
  const formattedFirstEntry = firstEntryDate
    ? formatDate(firstEntryDate)
    : null;

  const [daysSinceSignup, setDaysSinceSignup] = useState<number | null>(null);

  useEffect(() => {
    const days = Math.floor(
      (Date.now() - new Date(signupDate).getTime()) / (1000 * 60 * 60 * 24),
    );
    setDaysSinceSignup(days);
  }, [signupDate]);

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center space-x-6">
          <div className="flex-shrink-0">
            {image ? (
              <Image
                src={image}
                alt={`${name}'s avatar`}
                width={80}
                height={80}
                className="rounded-full"
              />
            ) : (
              <div className="w-20 h-20 bg-lotus-500/20 rounded-full flex items-center justify-center">
                <User size={32} className="text-lotus-400" />
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-dark-50 truncate">{name}</h1>
            <p className="text-dark-400 mt-1">{email}</p>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-dark-400">Member since:</span>
                <p className="font-medium text-dark-200">
                  {formattedSignupDate}
                </p>
                {daysSinceSignup !== null && (
                  <p className="text-xs text-dark-500">
                    {daysSinceSignup} days ago
                  </p>
                )}
              </div>

              {firstEntryDate && (
                <div>
                  <span className="text-dark-400">First journal entry:</span>
                  <p className="font-medium text-dark-200">
                    {formattedFirstEntry}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
