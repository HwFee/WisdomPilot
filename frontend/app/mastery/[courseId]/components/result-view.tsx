"use client";

import { ArrowLeft, Trophy, CheckCircle, XCircle } from "lucide-react";
import type { EnhancedQuizSubmitResponse } from "@/types/api";

interface ResultViewProps {
  finalResult: EnhancedQuizSubmitResponse;
  onBackToChapters: () => void;
}

export function ResultView({ finalResult, onBackToChapters }: ResultViewProps) {
  const passed = finalResult.passed;
  const accuracy = Math.round(finalResult.accuracy * 100);

  return (
    <div className="min-h-screen bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 text-muted-foreground">
            <ArrowLeft className="size-4" strokeWidth={1.5} />
            <span className="text-sm">返回</span>
          </div>
          <div className="flex items-center gap-2">
            <Trophy className="size-5 text-amber-600" strokeWidth={1.5} />
            <span className="font-semibold">测试结果</span>
          </div>
          <div className="w-20"></div>
        </div>
      </header>

      <main className="pt-24 pb-12 px-4">
        <div className="max-w-md mx-auto">
          <div
            className={`rounded-lg border p-8 text-center mb-6 bg-card ${
              passed ? "border-emerald-600" : "border-red-600"
            }`}
          >
            <div>
              {passed ? (
                <CheckCircle
                  className="size-20 text-emerald-600 mx-auto mb-4"
                  strokeWidth={1.5}
                />
              ) : (
                <XCircle
                  className="size-20 text-red-600 mx-auto mb-4"
                  strokeWidth={1.5}
                />
              )}
            </div>

            <h2 className="text-2xl font-semibold text-foreground mb-2">
              {passed ? "恭喜通过！" : "继续努力"}
            </h2>

            <p className="text-muted-foreground mb-6">
              {finalResult.total_questions > 0 && (
                <>
                  答对 {finalResult.correct_answers}/
                  {finalResult.total_questions} 题 ({accuracy}%)
                </>
              )}
            </p>

            <div className="bg-muted rounded-lg p-4 mb-6 flex flex-col gap-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">获得经验值</span>
                <span className="font-medium text-primary">
                  +{finalResult.xp_earned}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">掌握点数</span>
                <span className="font-medium text-amber-600">
                  +{finalResult.mastery_points_earned}
                </span>
              </div>
            </div>

            {finalResult.recommendations.length > 0 && (
              <div className="bg-muted rounded-lg p-4 text-left text-sm">
                <p className="font-medium text-foreground mb-2">学习建议</p>
                <ul className="text-muted-foreground space-y-1">
                  {finalResult.recommendations.map((rec) => (
                    <li key={rec}>• {rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <button
            onClick={onBackToChapters}
            className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            返回章节列表
          </button>
        </div>
      </main>
    </div>
  );
}
