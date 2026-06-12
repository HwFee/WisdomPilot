"use client";

import { CheckCircle, XCircle } from "lucide-react";
import type { BaseQuestionResponse } from "@/types/api";
import { getQuestionType } from "../types";

interface AnswerAreaProps {
  currentQuestion: BaseQuestionResponse;
  baseAnswers: Map<number, string>;
  setBaseAnswers: React.Dispatch<React.SetStateAction<Map<number, string>>>;
  submitted: boolean;
  isCorrect: boolean;
}

export function AnswerArea({
  currentQuestion,
  baseAnswers,
  setBaseAnswers,
  submitted,
  isCorrect,
}: AnswerAreaProps) {
  return (
    <div className="col-span-12 lg:col-span-7 space-y-6">
      {getQuestionType(currentQuestion) === "choice" &&
        currentQuestion.options &&
        currentQuestion.options.length > 0 && (
          <div className="flex flex-col gap-y-3">
            {currentQuestion.options.map((option, index) => {
              const optionLabel = String.fromCharCode(65 + index);
              const isSelected = baseAnswers.get(currentQuestion.id) === optionLabel;
              const isCorrectOption =
                currentQuestion.correct_answer?.toUpperCase() === optionLabel;

              return (
                <button
                  type="button"
                  key={optionLabel}
                  onClick={() =>
                    !submitted &&
                    setBaseAnswers((prev) =>
                      new Map(prev).set(currentQuestion.id, optionLabel),
                    )
                  }
                  disabled={submitted}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                    submitted
                      ? isSelected
                        ? isCorrect
                          ? "border-emerald-600 bg-muted"
                          : "border-red-600 bg-muted"
                        : isCorrectOption
                          ? "border-emerald-600 bg-muted"
                          : "border-border opacity-50"
                      : isSelected
                        ? "border-primary bg-muted"
                        : "border-border hover:border-muted hover:bg-muted"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`size-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                        submitted
                          ? isSelected && isCorrect
                            ? "bg-emerald-600 text-primary-foreground"
                            : isSelected && !isCorrect
                              ? "bg-red-600 text-primary-foreground"
                              : isCorrectOption
                                ? "bg-emerald-600 text-primary-foreground"
                                : "bg-muted text-muted-foreground"
                          : isSelected
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {submitted && isCorrectOption ? (
                        <CheckCircle className="size-4" strokeWidth={1.5} />
                      ) : (
                        optionLabel
                      )}
                    </span>
                    <span className="text-foreground">{option}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}

      {getQuestionType(currentQuestion) === "fill_blank" && (
        <div className="flex flex-col gap-y-4">
          <div className="bg-card rounded-lg border border-border p-4">
            <label htmlFor="fill-blank-answer" className="block text-sm font-medium text-foreground mb-2">
              请输入答案：
            </label>
            <input
              id="fill-blank-answer"
              type="text"
              value={baseAnswers.get(currentQuestion.id) || ""}
              onChange={(event) =>
                !submitted &&
                setBaseAnswers((prev) =>
                  new Map(prev).set(currentQuestion.id, event.target.value),
                )
              }
              disabled={submitted}
              placeholder="在此输入您的答案..."
              className={`w-full p-4 rounded-lg border-2 bg-background text-foreground transition-all ${
                submitted
                  ? isCorrect
                    ? "border-emerald-600 bg-muted"
                    : "border-red-600 bg-muted"
                  : "border-border focus:border-primary focus:outline-none"
              } disabled:opacity-70`}
            />
          </div>

          {submitted && (
            <div className="p-4 rounded-lg bg-muted">
              <p className="text-sm font-medium text-foreground mb-1 flex items-center gap-1">
                {isCorrect ? (
                  <>
                    <CheckCircle className="size-4 text-emerald-600" strokeWidth={1.5} />
                    正确！
                  </>
                ) : (
                  <>
                    <XCircle className="size-4 text-red-600" strokeWidth={1.5} />
                    错误
                  </>
                )}
              </p>
              <p className="text-sm text-muted-foreground">
                正确答案：
                <span className="font-medium text-emerald-600">
                  {currentQuestion.correct_answer}
                </span>
              </p>
            </div>
          )}
        </div>
      )}

      {submitted && currentQuestion.explanation && (
        <div className="mt-6 p-4 rounded-lg bg-muted">
          <p className="text-sm font-medium text-foreground mb-2">解析</p>
          <p className="text-sm text-muted-foreground">
            {currentQuestion.explanation}
          </p>
        </div>
      )}
    </div>
  );
}
