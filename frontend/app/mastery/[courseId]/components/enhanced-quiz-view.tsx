"use client";

import { ArrowLeft, Zap, CheckCircle } from "lucide-react";
import type { EnhancedQuizQuestion } from "@/types/api";
import { DIFFICULTY_COLORS } from "../types";

interface EnhancedQuizViewProps {
  enhancedQuestions: EnhancedQuizQuestion[];
  currentQuestionIndex: number;
  enhancedAnswers: Map<string, string>;
  enhancedLoading: boolean;
  generationStatus: "idle" | "generating" | "completed" | "failed";
  generationProgress: { current: number; total: number };
  submitted: boolean;
  isCorrect: boolean;
  setEnhancedAnswers: React.Dispatch<React.SetStateAction<Map<string, string>>>;
  onSubmit: () => void;
  onNext: () => void;
  onBackToChapters: () => void;
}

export function EnhancedQuizView(props: EnhancedQuizViewProps) {
  const {
    enhancedQuestions, currentQuestionIndex, enhancedAnswers, enhancedLoading,
    generationStatus, generationProgress, submitted, isCorrect,
    onSubmit, onNext, onBackToChapters, setEnhancedAnswers,
  } = props;

  const currentQuestion = enhancedQuestions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === enhancedQuestions.length - 1;

  return (
    <div className="min-h-screen bg-background">
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <button type="button"
          onClick={onBackToChapters}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          <span className="text-sm">退出</span>
        </button>
        <div className="flex items-center gap-2">
          <Zap className="size-5 text-amber-500" />
          <span className="font-semibold">强化测试</span>
        </div>
        <div className="flex items-center gap-1">
          {enhancedQuestions.map((q, i) => (
            <div
              key={q.id}
              className={`size-2 rounded-full transition-colors ${
                i < currentQuestionIndex
                  ? "bg-emerald-400"
                  : i === currentQuestionIndex
                    ? "bg-primary"
                    : "bg-muted"
              }`}
            />
          ))}
        </div>
      </div>
    </header>

    <main className="pt-20 pb-24 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Question header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium">
            {currentQuestionIndex + 1} / {enhancedQuestions.length}
          </span>
          <span
            className={`px-3 py-1 rounded-lg text-xs font-medium border ${DIFFICULTY_COLORS[currentQuestion.difficulty]}`}
          >
            难度 {currentQuestion.difficulty}
          </span>
          <span className="text-xs text-muted-foreground">强化题</span>
        </div>

        {/* Question */}
        <div className="bg-card rounded-2xl border border-border p-6 mb-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">
            {currentQuestion.text}
          </h2>

          {currentQuestion.knowledge_points.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {currentQuestion.knowledge_points.map((kp) => (
                <span
                  key={kp}
                  className="px-2 py-1 bg-orange-500/10 text-orange-400 text-xs rounded-full"
                >
                  {kp}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Options */}
        {currentQuestion.options && (
          <div className="flex flex-col gap-y-3">
            {currentQuestion.options.map((opt, i) => {
              const optLabel = String.fromCharCode(65 + i);
              const isSelected = enhancedAnswers.get(currentQuestion.id) === optLabel;
              const isCorrectOption = currentQuestion.correct_answer?.toUpperCase() === optLabel;

              return (
                <button type="button"
                  key={optLabel}
                  onClick={() =>
                    !submitted &&
                    setEnhancedAnswers((prev) =>
                      new Map(prev).set(currentQuestion.id, optLabel),
                    )
                  }
                  disabled={submitted}
                  className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                    submitted
                      ? isSelected
                        ? isCorrect
                          ? "border-emerald-500 bg-emerald-500/10"
                          : "border-red-500 bg-red-500/10"
                        : isCorrectOption
                          ? "border-emerald-500 bg-emerald-500/5"
                          : "border-border opacity-50"
                      : isSelected
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-muted hover:bg-muted/30"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`size-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                        submitted
                          ? isSelected && isCorrect
                            ? "bg-emerald-500 text-white"
                            : isSelected && !isCorrect
                              ? "bg-red-500 text-white"
                              : isCorrectOption
                                ? "bg-emerald-500 text-white"
                                : "bg-muted text-muted-foreground"
                          : isSelected
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {submitted && isCorrectOption ? (
                        <CheckCircle className="size-4" />
                      ) : (
                        optLabel
                      )}
                    </span>
                    <span className="text-foreground">{opt}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </main>

    {/* Bottom action bar */}
    <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
      <div className="max-w-2xl mx-auto p-4">
        <button type="button"
          onClick={
            submitted
              ? onNext
              : onSubmit
          }
          disabled={
            !enhancedAnswers.get(currentQuestion.id) || enhancedLoading || (submitted && isLastQuestion && generationStatus !== "completed" && enhancedQuestions.length < generationProgress.total)
          }
          className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {enhancedLoading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="size-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              提交中...
            </span>
          ) : submitted ? (
            isLastQuestion ? (
              generationStatus === "completed" || enhancedQuestions.length >= generationProgress.total ? (
                "完成测试"
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <div className="size-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  正在生成更多题目...
                </span>
              )
            ) : (
              "下一题"
            )
          ) : (
            "提交答案"
          )}
        </button>
      </div>
    </div>
    </div>
  );
}
