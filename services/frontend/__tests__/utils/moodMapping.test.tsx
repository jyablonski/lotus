import {
  moodToInt,
  intToMood,
  getMoodConfig,
  getMoodConfigByInt,
  getAllMoodOptions,
  MOOD_CONFIGS,
} from "@/lib/utils/moodMapping";

describe("Mood Mapping Utils", () => {
  // Existing tests (preserved)
  test("converts mood string to integer", () => {
    expect(moodToInt("happy")).toBe(7);
    expect(moodToInt("sad")).toBe(3);
    expect(moodToInt("neutral")).toBe(5);
  });

  test("converts integer to mood string", () => {
    expect(intToMood(7)).toBe("happy");
    expect(intToMood(3)).toBe("sad");
    expect(intToMood(5)).toBe("neutral");
  });

  test("gets mood config", () => {
    const config = getMoodConfig("happy");
    expect(config.label).toBe("Happy");
    expect(config.emoji).toBe("😊");
    expect(config.value).toBe(7);
  });

  // ── New tests ─────────────────────────────────────────────────────────

  describe("moodToInt edge cases", () => {
    test("returns 5 (neutral) for unknown mood key", () => {
      expect(moodToInt("unknown")).toBe(5);
      expect(moodToInt("")).toBe(5);
    });

    test("converts all known mood keys", () => {
      expect(moodToInt("excited")).toBe(8);
      expect(moodToInt("happy")).toBe(7);
      expect(moodToInt("content")).toBe(6);
      expect(moodToInt("neutral")).toBe(5);
      expect(moodToInt("tired")).toBe(4);
      expect(moodToInt("sad")).toBe(3);
      expect(moodToInt("anxious")).toBe(2);
      expect(moodToInt("angry")).toBe(1);
    });
  });

  describe("intToMood edge cases", () => {
    test('returns "neutral" for unknown integer', () => {
      expect(intToMood(99)).toBe("neutral");
      expect(intToMood(0)).toBe("neutral");
      expect(intToMood(-1)).toBe("neutral");
    });

    test("converts all known integers", () => {
      expect(intToMood(8)).toBe("excited");
      expect(intToMood(7)).toBe("happy");
      expect(intToMood(6)).toBe("content");
      expect(intToMood(5)).toBe("neutral");
      expect(intToMood(4)).toBe("tired");
      expect(intToMood(3)).toBe("sad");
      expect(intToMood(2)).toBe("anxious");
      expect(intToMood(1)).toBe("angry");
    });
  });

  describe("getMoodConfig edge cases", () => {
    test("returns neutral config for unknown key", () => {
      const config = getMoodConfig("nonexistent");
      expect(config.label).toBe("Neutral");
      expect(config.value).toBe(5);
    });
  });

  describe("getMoodConfigByInt", () => {
    test("returns correct config for each mood value", () => {
      expect(getMoodConfigByInt(8).label).toBe("Excited");
      expect(getMoodConfigByInt(7).label).toBe("Happy");
      expect(getMoodConfigByInt(6).label).toBe("Content");
      expect(getMoodConfigByInt(5).label).toBe("Neutral");
      expect(getMoodConfigByInt(4).label).toBe("Tired");
      expect(getMoodConfigByInt(3).label).toBe("Sad");
      expect(getMoodConfigByInt(2).label).toBe("Anxious");
      expect(getMoodConfigByInt(1).label).toBe("Angry");
    });

    test("returns neutral config for out-of-range value", () => {
      expect(getMoodConfigByInt(0).label).toBe("Neutral");
      expect(getMoodConfigByInt(99).label).toBe("Neutral");
    });

    test("includes emoji and color in config", () => {
      const config = getMoodConfigByInt(8);
      expect(config.emoji).toBe("🤩");
      expect(config.color).toBeTruthy();
    });
  });

  describe("getAllMoodOptions", () => {
    test("returns all 8 mood options", () => {
      const options = getAllMoodOptions();
      expect(options).toHaveLength(8);
    });

    test("each option has key, value, label, emoji, and color", () => {
      const options = getAllMoodOptions();
      options.forEach((option) => {
        expect(option.key).toBeTruthy();
        expect(option.value).toBeGreaterThanOrEqual(1);
        expect(option.value).toBeLessThanOrEqual(8);
        expect(option.label).toBeTruthy();
        expect(option.emoji).toBeTruthy();
        expect(option.color).toBeTruthy();
      });
    });

    test("includes all mood keys from MOOD_CONFIGS", () => {
      const options = getAllMoodOptions();
      const keys = options.map((o) => o.key);
      Object.keys(MOOD_CONFIGS).forEach((key) => {
        expect(keys).toContain(key);
      });
    });
  });
});
