module.exports = {
  testEnvironment: "jsdom",
  testMatch: ["**/__tests__/**/*.test.js", "**/?(*.)+(spec|test).js"],
  collectCoverageFrom: [
    "script.js",
    "!node_modules/**",
    "!coverage/**"
  ],
  coverageDirectory: "coverage",
  verbose: true
};
