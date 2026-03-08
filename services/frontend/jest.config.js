const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

// add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jsdom",
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "<rootDir>/__tests__/__mocks__/",
    "<rootDir>/e2e/",
    "<rootDir>/__tests__/contract/",
  ],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    "^server-only$": "<rootDir>/__tests__/__mocks__/server-only.js",
  },
  collectCoverageFrom: [
    "components/**/*.{js,jsx,ts,tsx}",
    "app/**/*.{js,jsx,ts,tsx}",
    "hooks/**/*.{js,jsx,ts,tsx}",
    "lib/**/*.{js,jsx,ts,tsx}",
    "types/**/*.{js,jsx,ts,tsx}",
    "actions/**/*.{js,jsx,ts,tsx}",
    "!**/*.d.ts",
    "!**/jest.setup.js",
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "text-summary", "lcov"],
  // Fail the build if coverage drops below these thresholds
  coverageThreshold: {
    global: {
      statements: 70,
      branches: 65,
      functions: 70,
      lines: 70,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
