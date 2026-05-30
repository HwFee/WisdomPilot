/**
 * Code Execution API - Judge0 code execution endpoints
 */

import {
  CodeExecutionRequest,
  CodeExecutionResponse,
  LanguageInfo,
} from '@/types/api'
import { get, post } from './client'

// Longer timeout for code execution (Judge0 can be slow)
const CODE_EXECUTION_TIMEOUT = 60000 // 60 seconds

// ========================================
// Types
// ========================================

export interface TestCaseInput {
  input: string
  expected_output: string
}

export interface TestCaseResult {
  passed: boolean
  input: string
  expected: string
  actual: string
  message?: string
}

export interface BatchCodeExecutionRequest {
  code: string
  language_id: number
  test_cases: TestCaseInput[]
}

export interface BatchCodeExecutionResponse {
  token: string
  status: string
  status_id: number
  passed_count: number
  total_count: number
  results: TestCaseResult[]
  time?: string
  memory?: number
  compile_output?: string
  message?: string
}

// ========================================
// Code Execution
// ========================================

export async function executeCode(
  request: CodeExecutionRequest,
  token: string
): Promise<CodeExecutionResponse> {
  return post<CodeExecutionResponse>('/api/code/execute', token, request, CODE_EXECUTION_TIMEOUT)
}

export async function executeCodeBatch(
  request: BatchCodeExecutionRequest,
  authToken: string
): Promise<BatchCodeExecutionResponse> {
  return post<BatchCodeExecutionResponse>('/api/code/execute-batch', authToken, request, CODE_EXECUTION_TIMEOUT)
}

export async function getSupportedLanguages(token: string): Promise<LanguageInfo[]> {
  return get<LanguageInfo[]>('/api/code/languages', token)
}

// Re-export types
export type { CodeExecutionRequest, CodeExecutionResponse, LanguageInfo }
