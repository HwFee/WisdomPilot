"use client";

import { ArrowLeft, Target, Zap, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import type { BaseAnswersSubmitResponse } from "@/types/api";

interface AnalysisViewProps {
  baseResult: BaseAnswersSubmitResponse;
  enhancedLoading: boolean;
  onStartEnhancedQuiz: () => void;
  onBackToChapters: () => void;
  onViewQuestions: () => void;
}

export function AnalysisView(props: AnalysisViewProps) {
  const { baseResult, enhancedLoading, onStartEnhancedQuiz, onBackToChapters, onViewQuestions } = props;
  const accuracy = Math.round(baseResult.accuracy * 100);

  return (
    <div className="min-h-screen bg-background">
    <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <button type="button"
          onClick={onViewQuestions}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" strokeWidth={1.5} />
          <span className="text-sm">查看题目</span>
        </button>
        <div className="flex items-center gap-2">
          <Target className="size-5 text-amber-600" strokeWidth={1.5} />
          <span className="font-semibold">学习分析</span>
        </div>
        <button type="button"
          onClick={onBackToChapters}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          退出
        </button>
      </div>
    </header>

    <main className="pt-24 pb-12 px-4">
      <div className="max-w-md mx-auto">
        {/* Summary */}
        <div className="bg-card rounded-lg border border-border p-6 mb-6">
          <div className="text-center mb-6">
            <p className="text-4xl font-bold text-foreground mb-2">
              {accuracy}%
            </p>
            <p className="text-muted-foreground">基础测试正确率</p>
          </div>

          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="bg-muted rounded-lg p-3">
              <p className="text-2xl font-bold text-emerald-600">
                {baseResult.correct_answers}
              </p>
              <p className="text-xs text-muted-foreground">正确</p>
            </div>
            <div className="bg-muted rounded-lg p-3">
              <p className="text-2xl font-bold text-red-600">
                {baseResult.total_questions - baseResult.correct_answers}
              </p>
              <p className="text-xs text-muted-foreground">错误</p>
            </div>
          </div>
        </div>

        {/* Weak points */}
        {baseResult.weak_points.length > 0 && (
          <div className="bg-muted rounded-lg border border-border p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="size-5 text-amber-600" strokeWidth={1.5} />
              <span className="font-medium text-foreground">
                需要强化的知识点
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {baseResult.weak_points.map((point) => (
                <span
                  key={point}
                  className="px-3 py-1 bg-secondary text-amber-600 rounded-lg text-sm"
                >
                  {point}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Strong points */}
        {baseResult.strong_points.length > 0 && (
          <div className="bg-muted rounded-lg border border-border p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="size-5 text-emerald-600" strokeWidth={1.5} />
              <span className="font-medium text-foreground">
                已掌握的知识点
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {baseResult.strong_points.map((point) => (
                <span
                  key={point}
                  className="px-3 py-1 bg-secondary text-emerald-600 rounded-lg text-sm"
                >
                  {point}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <button type="button"
          onClick={onStartEnhancedQuiz}
          disabled={enhancedLoading}
          className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
        >
          {enhancedLoading ? (
            <>
              <Loader2 className="size-5" strokeWidth={1.5} />
              生成强化测试...
            </>
          ) : (
            <>
              <Zap className="size-5" strokeWidth={1.5} />
              开始强化测试
            </>
          )}
        </button>

        <button type="button"
          onClick={onBackToChapters}
          className="w-full mt-3 py-3 bg-card border border-border rounded-lg font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          暂时跳过，返回章节
        </button>
      </div>
    </main>
    </div>
  );
}
