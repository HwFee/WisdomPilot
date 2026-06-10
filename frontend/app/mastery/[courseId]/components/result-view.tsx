"use client";

import { ArrowLeft, Trophy, CheckCircle, XCircle } from "lucide-react";
import { LazyMotion, domAnimation, m } from "framer-motion";
import type { EnhancedQuizSubmitResponse } from "@/types/api";

interface ResultViewProps {
  finalResult: EnhancedQuizSubmitResponse;
  onBackToChapters: () => void;
}

export function ResultView({ finalResult, onBackToChapters }: ResultViewProps) {
  const passed = finalResult.passed;
  const accuracy = Math.round(finalResult.accuracy * 100);

  return (
    <LazyMotion features={domAnimation}>
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-2 text-muted-foreground">
              <ArrowLeft className="size-4" />
              <span className="text-sm">返回</span>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="size-5 text-amber-500" />
              <span className="font-semibold">测试结果</span>
            </div>
            <div className="w-20"></div>
          </div>
        </header>

        <main className="pt-24 pb-12 px-4">
          <div className="max-w-md mx-auto">
            <m.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className={`rounded-2xl border p-8 text-center mb-6 ${
                passed
                  ? "bg-emerald-500/10 border-emerald-500/30"
                  : "bg-orange-500/10 border-orange-500/30"
              }`}
            >
              <m.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 20,
                  delay: 0.2,
                }}
              >
                {passed ? (
                  <CheckCircle className="size-20 text-emerald-500 mx-auto mb-4" />
                ) : (
                  <XCircle className="size-20 text-orange-400 mx-auto mb-4" />
                )}
              </m.div>

              <m.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-2xl font-semibold text-foreground mb-2"
              >
                {passed ? "恭喜通过！" : "继续努力"}
              </m.h2>

              <m.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="text-muted-foreground mb-6"
              >
                {finalResult.total_questions > 0 && (
                  <>
                    答对 {finalResult.correct_answers}/
                    {finalResult.total_questions} 题 ({accuracy}%)
                  </>
                )}
              </m.p>

              <m.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-card rounded-xl p-4 mb-6 flex flex-col gap-y-3"
              >
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">获得经验值</span>
                  <span className="font-medium text-blue-500">
                    +{finalResult.xp_earned}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">掌握点数</span>
                  <span className="font-medium text-amber-500">
                    +{finalResult.mastery_points_earned}
                  </span>
                </div>
              </m.div>

              {finalResult.recommendations.length > 0 && (
                <m.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="bg-muted/50 rounded-xl p-4 text-left text-sm"
                >
                  <p className="font-medium text-foreground mb-2">学习建议</p>
                  <ul className="text-muted-foreground space-y-1">
                    {finalResult.recommendations.map((rec) => (
                      <li key={rec}>• {rec}</li>
                    ))}
                  </ul>
                </m.div>
              )}
            </m.div>

            <m.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={onBackToChapters}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 transition-all"
            >
              返回章节列表
            </m.button>
          </div>
        </main>
      </div>
    </LazyMotion>
  );
}
