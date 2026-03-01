import { trackEvent, getTimeOfDay, countWords } from "@/lib/analytics";

// ---------------------------------------------------------------------------
// trackEvent
// ---------------------------------------------------------------------------

describe("trackEvent", () => {
  afterEach(() => {
    // Restore window.gtag between tests
    if (typeof window !== "undefined") {
      delete (window as unknown as Record<string, unknown>).gtag;
    }
  });

  it("calls window.gtag when it is available", () => {
    const mockGtag = jest.fn();
    window.gtag = mockGtag;

    trackEvent("test_event", { key: "value" });

    expect(mockGtag).toHaveBeenCalledWith("event", "test_event", {
      key: "value",
    });
  });

  it("passes empty params object by default", () => {
    const mockGtag = jest.fn();
    window.gtag = mockGtag;

    trackEvent("bare_event");

    expect(mockGtag).toHaveBeenCalledWith("event", "bare_event", {});
  });

  it("does not throw when window.gtag is undefined", () => {
    delete (window as unknown as Record<string, unknown>).gtag;

    expect(() => trackEvent("no_gtag_event")).not.toThrow();
  });

  it("does not throw when window.gtag is not a function", () => {
    (window as unknown as Record<string, unknown>).gtag = "not-a-function";

    expect(() => trackEvent("bad_gtag")).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// getTimeOfDay
// ---------------------------------------------------------------------------

describe("getTimeOfDay", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  const cases: [number, "morning" | "afternoon" | "evening" | "night"][] = [
    // Night: 21–04
    [0, "night"],
    [3, "night"],
    [4, "night"],
    [21, "night"],
    [23, "night"],
    // Morning: 05–11
    [5, "morning"],
    [8, "morning"],
    [11, "morning"],
    // Afternoon: 12–16
    [12, "afternoon"],
    [14, "afternoon"],
    [16, "afternoon"],
    // Evening: 17–20
    [17, "evening"],
    [19, "evening"],
    [20, "evening"],
  ];

  it.each(cases)("hour %i → %s", (hour, expected) => {
    jest.spyOn(Date.prototype, "getHours").mockReturnValue(hour);
    expect(getTimeOfDay()).toBe(expected);
  });
});

// ---------------------------------------------------------------------------
// countWords
// ---------------------------------------------------------------------------

describe("countWords", () => {
  it("counts words in a normal sentence", () => {
    expect(countWords("hello world")).toBe(2);
  });

  it("handles multiple spaces between words", () => {
    expect(countWords("one   two    three")).toBe(3);
  });

  it("handles leading and trailing whitespace", () => {
    expect(countWords("  padded text  ")).toBe(2);
  });

  it("handles tabs and newlines", () => {
    expect(countWords("line one\nline\ttwo")).toBe(4);
  });

  it("returns 0 for an empty string", () => {
    expect(countWords("")).toBe(0);
  });

  it("returns 0 for whitespace-only input", () => {
    expect(countWords("   \n\t  ")).toBe(0);
  });

  it("counts a single word", () => {
    expect(countWords("hello")).toBe(1);
  });
});
