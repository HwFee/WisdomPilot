"use client";

import { Button } from "@/components/ui/button";
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
    <Button
      type="button"
      size="lg"
      onClick={onSubmit}
      disabled={!baseAnswers.get(currentQuestion.id)}
      className="w-full py-4"
    >
      提交答案
    </Button>
  );
}
