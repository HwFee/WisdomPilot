import { deckCall } from './client'
import { getMockCertHome, getMockExam, submitMockExam } from './mock/certification'
import type { CertAnswer, CertExam, CertResult, CertificationHome } from './types'

/** GET /api/certification/home —— 徽章墙 + 可考列表 */
export function getCertificationHome(): Promise<CertificationHome> {
  return deckCall('/certification/home', () => getMockCertHome())
}

/** GET /api/certification/exam?id= —— 取试卷（id=placement 为定级测试） */
export function getExam(id: string): Promise<CertExam> {
  return deckCall(`/certification/exam?id=${encodeURIComponent(id)}`, () => getMockExam(id))
}

/** POST /api/certification/submit —— 交卷判分 */
export function submitExam(examId: string, answers: CertAnswer[]): Promise<CertResult> {
  return deckCall('/certification/submit', () => submitMockExam(examId, answers), {
    method: 'POST',
    body: JSON.stringify({ exam_id: examId, answers }),
  })
}
