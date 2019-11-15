const { defaults: tsjPreset } = require("ts-jest/presets");

module.exports = {
  transform: {
    ...tsjPreset.transform
  },
  testMatch: ["<rootDir>/src/**/*.test.ts"],
  coverageReporters: ["lcov", "text-summary"],
  collectCoverage: true,
  collectCoverageFrom: ["<rootDir>/src/**/*.ts", "!<rootDir>/src/index.ts"],
  preset: "ts-jest",
  roots: ["<rootDir>/src"],
  testEnvironment: "node"
};
