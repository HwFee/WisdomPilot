"use client";

import { PartyPopper } from "lucide-react";
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
  return (
    <div
      className={`fixed bottom-0 left-0 right-0 border-t transition-colors ${
        submitted
          ? isCorrect
            ? "bg-muted border-emerald-600/30"
            : "bg-muted border-red-600/20"
          : "bg-card border-border"
      }`}
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
