"use client";

import { useState, useCallback } from "react";
import type { BaseQuestionResponse } from "@/types/api";
import { getQuestionType } from "./types";

export function useBaseQuiz() {
  const [baseAnswers, setBaseAnswers] = useState<Map<number, string>>(
    new Map(),
  );
  const [submitted, setSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [completedQuestionsMap, setCompletedQuestionsMap] = useState<
    Map<number, boolean>
  >(new Map());
  const checkAnswer = useCallback(
    (question: BaseQuestionResponse, answer: string): boolean => {
      const questionType = getQuestionType(question);
      if (questionType === "choice") {
        return (
          answer.toUpperCase() === question.correct_answer?.toUpperCase()
        );
      }
      // fill_blank
      const userAnswer = answer.trim().toLowerCase();
      const correctAnswer = question.correct_answer?.trim() || "";
      const acceptedForms = correctAnswer
        .split("|")
        .flatMap((s) => {
          const trimmed = s.trim();
          return trimmed ? [trimmed] : [];
        });
      return acceptedForms.some((form) => {
        const lower = form.toLowerCase();
        if (lower.includes(";")) {
          const parts = lower
            .split(";")
            .flatMap((p) => {
              const trimmed = p.trim();
              return trimmed ? [trimmed] : [];
            });
          return parts.every((p) => userAnswer.includes(p));
        }
        return userAnswer === lower;
      });
    },
    [],
  );

  const restoreSubmitState = useCallback(
    (questionId: number, map: Map<number, boolean>) => {
      if (map.has(questionId)) {
        setSubmitted(true);
        setIsCorrect(map.get(questionId) || false);
      } else {
        setSubmitted(false);
        setIsCorrect(false);
      }
    },
    [],
  );

  return {
    baseAnswers,
    setBaseAnswers,
    submitted,
    setSubmitted,
    isCorrect,
    setIsCorrect,
    completedQuestionsMap,
    setCompletedQuestionsMap,
    checkAnswer,
    restoreSubmitState,
  };
}
