"use client";

import { CheckCircle, ChevronRight, Loader2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SubmittedQuizActionBarProps {
  isCorrect: boolean;
  isLastQuestion: boolean;
  baseQuestionLoading: boolean;
  onNext: () => void;
}

export function SubmittedQuizActionBar({
  isCorrect,
  isLastQuestion,
  baseQuestionLoading,
  onNext,
}: SubmittedQuizActionBarProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        {isCorrect ? (
          <>
            <CheckCircle className="size-6 text-emerald-600" strokeWidth={1.5} />
            <span className="font-medium text-emerald-600">
              正确！
            </span>
          </>
        ) : (
          <>
            <XCircle className="size-6 text-red-600" strokeWidth={1.5} />
            <span className="font-medium text-red-600">错误</span>
          </>
        )}
      </div>
      <Button
        size="lg"
        onClick={onNext}
        disabled={baseQuestionLoading}
        className="px-8 py-3 inline-flex items-center gap-2"
      >
        {baseQuestionLoading ? (
          <Loader2 className="size-4" strokeWidth={1.5} />
        ) : (
          <>
            {isLastQuestion ? "查看结果" : "下一题"}
            <ChevronRight className="size-4" strokeWidth={1.5} />
          </>
        )}
      </Button>
    </div>
  );
}
