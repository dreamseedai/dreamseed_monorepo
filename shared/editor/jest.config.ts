import type { Config } from 'jest'

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testRegex: '.*\\.test\\.ts$',
  moduleFileExtensions: ['ts', 'js']
}

export default config
