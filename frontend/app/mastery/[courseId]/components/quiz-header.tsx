"use client";

import { ArrowLeft, BookOpen } from "lucide-react";
import { PageContainer } from "@/components/layout";
import { QuestionNavigator } from "./question-navigator";
import type { BaseQuestionResponse } from "@/types/api";

interface QuizHeaderProps {
  selectedChapterTitle: string;
  onBackToChapters: () => void;
  baseQuestions: BaseQuestionResponse[];
  currentQuestionIndex: number;
  completedQuestionsMap: Map<number, boolean>;
  setCurrentQuestionIndex: React.Dispatch<React.SetStateAction<number>>;
  setSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
  setIsCorrect: React.Dispatch<React.SetStateAction<boolean>>;
}

export function QuizHeader({
  selectedChapterTitle,
  onBackToChapters,
  baseQuestions,
  currentQuestionIndex,
  completedQuestionsMap,
  setCurrentQuestionIndex,
  setSubmitted,
  setIsCorrect,
}: QuizHeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
      <PageContainer className="h-14 flex items-center justify-between">
        <button
          type="button"
          onClick={onBackToChapters}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" strokeWidth={1.5} />
          <span className="text-sm">退出</span>
        </button>
        <div className="flex items-center gap-2">
          <BookOpen className="size-5 text-amber-600" strokeWidth={1.5} />
          <span className="font-semibold">{selectedChapterTitle}</span>
        </div>
        <QuestionNavigator
          baseQuestions={baseQuestions}
          currentQuestionIndex={currentQuestionIndex}
          completedQuestionsMap={completedQuestionsMap}
          setCurrentQuestionIndex={setCurrentQuestionIndex}
          setSubmitted={setSubmitted}
          setIsCorrect={setIsCorrect}
        />
      </PageContainer>
    </header>
  );
}
