"use client";

import { PartyPopper } from "lucide-react";
import { cn } from "@/lib/utils";
import { PageContainer } from "@/components/layout";
import type { BaseQuestionResponse } from "@/types/api";
import { SubmittedQuizActionBar } from "./submitted-quiz-action-bar";
import { UnsubmittedQuizActionBar } from "./unsubmitted-quiz-action-bar";

interface QuizActionBarProps {
  submitted: boolean;
  isCorrect: boolean;
  isLastQuestion: boolean;
  baseQuestionLoading: boolean;
  currentQuestion: BaseQuestionResponse;
  baseAnswers: Map<number, string>;
  currentQuestionIndex: number;
  totalQuestions: number;
  onSubmit: () => void;
  onNext: () => void;
}

const FOOTER_STYLES = {
  idle: "bg-card border-border",
  correct: "bg-muted border-emerald-600/30",
  wrong: "bg-muted border-red-600/20",
} as const;

export function QuizActionBar({
  submitted,
  isCorrect,
  isLastQuestion,
  baseQuestionLoading,
  currentQuestion,
  baseAnswers,
  currentQuestionIndex,
  totalQuestions,
  onSubmit,
  onNext,
}: QuizActionBarProps) {
  const state = submitted ? (isCorrect ? "correct" : "wrong") : "idle";

  return (
    <div
      className={cn(
        "fixed bottom-0 left-0 right-0 border-t transition-colors",
        FOOTER_STYLES[state],
      )}
    >
      <PageContainer className="p-4">
        <div className="text-center text-sm text-muted-foreground mb-3">
          {isLastQuestion ? (
            <span className="text-amber-600 font-medium flex items-center justify-center gap-1">
              <PartyPopper className="size-4" strokeWidth={1.5} />
              完成本题即可获得经验奖励！
            </span>
          ) : (
            <span>进度: {currentQuestionIndex + 1}/{totalQuestions} · 完成所有题目可获得经验奖励</span>
          )}
        </div>
        {submitted ? (
          <SubmittedQuizActionBar
            isCorrect={isCorrect}
            isLastQuestion={isLastQuestion}
            baseQuestionLoading={baseQuestionLoading}
            onNext={onNext}
          />
        ) : (
          <UnsubmittedQuizActionBar
            currentQuestion={currentQuestion}
            baseAnswers={baseAnswers}
            onSubmit={onSubmit}
          />
        )}
      </PageContainer>
    </div>
  );
}
