const nextJest = require('next/jest')

// 安全审计修复：本机系统环境变量 NODE_ENV=production 会让 react-dom 加载
// production 构建（无 React.act），导致 @testing-library/react 报
// "React.act is not a function"。Jest 仅在 NODE_ENV 未定义时才默认设为 test，
// 这里显式强制，保证测试在任何宿主环境下加载开发构建。
process.env.NODE_ENV = 'test'

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  modulePathIgnorePatterns: ['<rootDir>/.next/'],
}

module.exports = createJestConfig(customJestConfig)
