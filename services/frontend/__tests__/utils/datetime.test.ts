import {
  formatEntryDate,
  formatShortDate,
  formatMonthYear,
  formatProfileDate,
  toTimezoneDateString,
} from "@/lib/utils/datetime";

describe("datetime formatting utilities", () => {
  // Use a known UTC timestamp: 2025-06-15T14:30:00Z
  const utcTimestamp = "2025-06-15T14:30:00Z";

  describe("formatEntryDate", () => {
    it("formats in Pacific Time", () => {
      const result = formatEntryDate(utcTimestamp, "America/Los_Angeles");
      // 14:30 UTC = 7:30 AM PT (during PDT)
      expect(result).toBe("Sunday, June 15, 7:30 AM");
    });

    it("formats in Eastern Time", () => {
      const result = formatEntryDate(utcTimestamp, "America/New_York");
      // 14:30 UTC = 10:30 AM ET (during EDT)
      expect(result).toBe("Sunday, June 15, 10:30 AM");
    });

    it("formats in UTC", () => {
      const result = formatEntryDate(utcTimestamp, "UTC");
      expect(result).toBe("Sunday, June 15, 2:30 PM");
    });
  });

  describe("formatShortDate", () => {
    it("formats as M/D/YYYY in the given timezone", () => {
      const result = formatShortDate(utcTimestamp, "America/Los_Angeles");
      expect(result).toBe("6/15/2025");
    });

    it("handles date boundary correctly", () => {
      // 2025-06-16T06:30:00Z = June 15 at 11:30 PM PT
      const lateUtc = "2025-06-16T06:30:00Z";
      const result = formatShortDate(lateUtc, "America/Los_Angeles");
      expect(result).toBe("6/15/2025");
    });
  });

  describe("formatMonthYear", () => {
    it("formats as 'Month YYYY'", () => {
      const date = new Date("2025-06-15T14:30:00Z");
      const result = formatMonthYear(date, "America/Los_Angeles");
      expect(result).toBe("June 2025");
    });
  });

  describe("formatProfileDate", () => {
    it("formats as 'Month D, YYYY'", () => {
      const result = formatProfileDate(utcTimestamp, "America/Los_Angeles");
      expect(result).toBe("June 15, 2025");
    });
  });

  describe("toTimezoneDateString", () => {
    it("returns YYYY-MM-DD in the given timezone", () => {
      const result = toTimezoneDateString(
        new Date("2025-06-16T06:30:00Z"),
        "America/Los_Angeles",
      );
      // 06:30 UTC = 11:30 PM PT on June 15
      expect(result).toBe("2025-06-15");
    });

    it("returns YYYY-MM-DD in UTC", () => {
      const result = toTimezoneDateString(
        new Date("2025-06-16T06:30:00Z"),
        "UTC",
      );
      expect(result).toBe("2025-06-16");
    });
  });
});
