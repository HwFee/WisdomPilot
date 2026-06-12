"use client";

import type { BaseQuestionResponse } from "@/types/api";

const MAX_VISIBLE_QUESTIONS = 5;
const CENTER_INDEX = 2;

interface QuestionNavigatorProps {
  baseQuestions: BaseQuestionResponse[];
  currentQuestionIndex: number;
  completedQuestionsMap: Map<number, boolean>;
  setCurrentQuestionIndex: React.Dispatch<React.SetStateAction<number>>;
  setSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
  setIsCorrect: React.Dispatch<React.SetStateAction<boolean>>;
}

export function QuestionNavigator({
  baseQuestions,
  currentQuestionIndex,
  completedQuestionsMap,
  setCurrentQuestionIndex,
  setSubmitted,
  setIsCorrect,
}: QuestionNavigatorProps) {
  let start = currentQuestionIndex - CENTER_INDEX;
  let end = start + MAX_VISIBLE_QUESTIONS;

  if (start < 0) {
    start = 0;
    end = Math.min(baseQuestions.length, MAX_VISIBLE_QUESTIONS);
  }

  if (end > baseQuestions.length) {
    end = baseQuestions.length;
    start = Math.max(0, end - MAX_VISIBLE_QUESTIONS);
  }

  return (
    <div className="flex items-center gap-1.5">
      {baseQuestions.slice(start, end).map((question, index) => {
        const globalIndex = start + index;
        const isCompleted = completedQuestionsMap.has(question.id);
        const wasCorrect = completedQuestionsMap.get(question.id) || false;
        const isCurrent = globalIndex === currentQuestionIndex;

        return (
          <button
            type="button"
            key={question.id}
            onClick={() => {
              if (completedQuestionsMap.has(question.id) || globalIndex <= currentQuestionIndex) {
                setCurrentQuestionIndex(globalIndex);
                if (completedQuestionsMap.has(question.id)) {
                  setSubmitted(true);
                  setIsCorrect(completedQuestionsMap.get(question.id) || false);
                } else {
                  setSubmitted(false);
                  setIsCorrect(false);
                }
              }
            }}
            title={`第 ${globalIndex + 1} 题`}
            className={`rounded-lg text-xs font-bold transition-all ${
              isCurrent
                ? "size-10 bg-primary text-primary-foreground"
                : isCompleted
                  ? wasCorrect
                    ? "size-8 bg-muted text-emerald-600 border-2 border-emerald-600"
                    : "size-8 bg-muted text-red-600 border-2 border-red-600"
                  : globalIndex <= currentQuestionIndex
                    ? "size-8 bg-muted text-muted-foreground border border-border hover:border-primary"
                    : "size-8 bg-muted text-muted-foreground/50 border border-border cursor-not-allowed"
            }`}
          >
            {globalIndex + 1}
          </button>
        );
      })}
    </div>
  );
}
