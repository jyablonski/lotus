import {
  MOOD_MIN,
  MOOD_MAX,
  MOOD_DEFAULT,
  clampMood,
  intToMood,
  getMoodConfigByInt,
  getAllMoodOptions,
} from "@/lib/utils/moodMapping";

describe("Mood Mapping Utils (1-10 scale)", () => {
  describe("constants", () => {
    test("MOOD_MIN is 1", () => expect(MOOD_MIN).toBe(1));
    test("MOOD_MAX is 10", () => expect(MOOD_MAX).toBe(10));
    test("MOOD_DEFAULT is 5", () => expect(MOOD_DEFAULT).toBe(5));
  });

  describe("clampMood", () => {
    test("clamps to 1-10", () => {
      expect(clampMood(1)).toBe(1);
      expect(clampMood(10)).toBe(10);
      expect(clampMood(5)).toBe(5);
    });
    test("clamps below 1 to 1", () => {
      expect(clampMood(0)).toBe(1);
      expect(clampMood(-1)).toBe(1);
    });
    test("clamps above 10 to 10", () => {
      expect(clampMood(11)).toBe(10);
      expect(clampMood(99)).toBe(10);
    });
    test("returns MOOD_DEFAULT for NaN", () => {
      expect(clampMood(Number.NaN)).toBe(MOOD_DEFAULT);
    });
  });

  describe("intToMood", () => {
    test("returns string of number for 1-10", () => {
      expect(intToMood(1)).toBe("1");
      expect(intToMood(10)).toBe("10");
      expect(intToMood(5)).toBe("5");
    });
    test("clamps out-of-range to valid key", () => {
      expect(intToMood(0)).toBe("1");
      expect(intToMood(99)).toBe("10");
    });
  });

  describe("getMoodConfigByInt", () => {
    test("returns label and color for 1-10", () => {
      expect(getMoodConfigByInt(5).label).toBe("5");
      expect(getMoodConfigByInt(1).label).toBe("1");
      expect(getMoodConfigByInt(10).label).toBe("10");
    });
    test("returns color string", () => {
      const config = getMoodConfigByInt(5);
      expect(config.color).toBeTruthy();
      expect(typeof config.color).toBe("string");
    });
    test("clamps out-of-range to valid config", () => {
      expect(getMoodConfigByInt(0).label).toBe("1");
      expect(getMoodConfigByInt(99).label).toBe("10");
    });
  });

  describe("getAllMoodOptions", () => {
    test("returns 10 options", () => {
      const options = getAllMoodOptions();
      expect(options).toHaveLength(10);
    });
    test("each option has key and label 1-10", () => {
      const options = getAllMoodOptions();
      options.forEach((option, i) => {
        const n = i + 1;
        expect(option.key).toBe(String(n));
        expect(option.label).toBe(String(n));
      });
    });
  });
});
