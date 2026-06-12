"use client";

import type { BaseQuestionResponse } from "@/types/api";

interface UnsubmittedQuizActionBarProps {
  currentQuestion: BaseQuestionResponse;
  baseAnswers: Map<number, string>;
  onSubmit: () => void;
}

export function UnsubmittedQuizActionBar({
  currentQuestion,
  baseAnswers,
  onSubmit,
}: UnsubmittedQuizActionBarProps) {
  return (
    <button
      type="button"
      onClick={onSubmit}
      disabled={!baseAnswers.get(currentQuestion.id)}
      className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      提交答案
    </button>
  );
}
