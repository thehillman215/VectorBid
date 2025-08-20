// Jest Configuration for VectorBid Testing Infrastructure
// Comprehensive testing setup for unit, integration, and accessibility tests

module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/utils/jest-setup.js'],
  
  // Test patterns
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.js',
    '<rootDir>/tests/integration/**/*.test.js',
    '<rootDir>/tests/accessibility/**/*.test.js',
    '<rootDir>/tests/performance/**/*.test.js'
  ],
  
  // Coverage collection
  collectCoverageFrom: [
    'app/static/js/**/*.js',
    '!app/static/js/**/*.min.js',
    '!**/node_modules/**',
    '!**/vendor/**'
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    },
    'app/static/js/interactive-demo.js': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    'app/static/js/error-handler.js': {
      branches: 75,
      functions: 75,
      lines: 75,
      statements: 75
    }
  },
  
  // Module name mapping for aliases
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/app/static/$1',
    '^@tests/(.*)$': '<rootDir>/tests/$1'
  },
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Transform configuration
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  
  // Setup files
  setupFiles: ['<rootDir>/tests/utils/global-setup.js'],
  
  // Test environment options
  testEnvironmentOptions: {
    url: 'http://localhost:8000'
  },
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ],
  
  // Coverage directory
  coverageDirectory: 'coverage',
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Restore mocks after each test
  restoreMocks: true,
  
  // Global variables available in tests
  globals: {
    'window': true,
    'document': true,
    'navigator': true,
    'fetch': true
  },
  
  // Error on deprecated features
  errorOnDeprecated: true,
  
  // Max workers for parallel test execution
  maxWorkers: '50%',
  
  // Notify mode
  notify: false,
  
  // Test results processor
  testResultsProcessor: '<rootDir>/tests/utils/test-results-processor.js'
};
