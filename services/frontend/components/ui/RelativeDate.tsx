"use client";

import { useState, useEffect } from "react";

interface RelativeDateProps {
  date: string;
  className?: string;
}

/**
 * Format date in a locale-independent way to avoid hydration mismatch
 */
function formatAbsoluteDate(dateString: string): string {
  const date = new Date(dateString);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const year = date.getFullYear();
  return `${month}/${day}/${year}`;
}

/**
 * Client component that displays relative dates
 * Shows absolute date on initial render, then updates to relative after hydration
 * This avoids hydration mismatches while still showing "2 hours ago" style dates
 */
export function RelativeDate({ date, className }: RelativeDateProps) {
  const [formattedDate, setFormattedDate] = useState<string>(() => {
    // Initial render: use absolute date (same on server and client)
    return formatAbsoluteDate(date);
  });

  useEffect(() => {
    // After hydration: update to relative date
    const updateDate = () => {
      const dateObj = new Date(date);
      const now = new Date();
      const diffInHours = Math.floor(
        (now.getTime() - dateObj.getTime()) / (1000 * 60 * 60),
      );

      if (diffInHours < 1) {
        setFormattedDate("Just now");
      } else if (diffInHours < 24) {
        setFormattedDate(`${diffInHours} hours ago`);
      } else {
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays === 1) {
          setFormattedDate("1 day ago");
        } else if (diffInDays < 7) {
          setFormattedDate(`${diffInDays} days ago`);
        } else {
          setFormattedDate(formatAbsoluteDate(date));
        }
      }
    };

    updateDate();

    // Optionally update every minute for "Just now" entries
    const interval = setInterval(updateDate, 60000);
    return () => clearInterval(interval);
  }, [date]);

  return <span className={className}>{formattedDate}</span>;
}
