"use client";

import { ArrowLeft, Trophy, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { EnhancedQuizSubmitResponse } from "@/types/api";
import { PageContainer, Grid, Panel, StatsGrid, StatCell } from "@/components/layout";

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
        <PageContainer className="h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 text-muted-foreground">
            <ArrowLeft className="size-4" strokeWidth={1.5} />
            <span className="text-sm">返回</span>
          </div>
          <div className="flex items-center gap-2">
            <Trophy className="size-5 text-amber-600" strokeWidth={1.5} />
            <span className="font-semibold">测试结果</span>
          </div>
          <div className="w-20" />
        </PageContainer>
      </header>

      <main className="pt-24 pb-12">
        <PageContainer>
          <Grid>
            <div className="col-span-12 lg:col-span-6 lg:col-start-4">
              <Panel className={`border-2 ${passed ? "border-emerald-600" : "border-red-600"}`}>
                <div className="p-8 text-center border-b border-border">
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

                  <p className="text-muted-foreground">
                    {finalResult.total_questions > 0 && (
                      <>
                        答对 {finalResult.correct_answers}/
                        {finalResult.total_questions} 题 ({accuracy}%)
                      </>
                    )}
                  </p>
                </div>

                <StatsGrid>
                  <StatCell>
                    <p className="text-2xl font-bold text-foreground">{accuracy}%</p>
                    <p className="text-xs text-muted-foreground mt-1">正确率</p>
                  </StatCell>
                  <StatCell>
                    <p className="text-2xl font-bold text-foreground">{finalResult.correct_answers}/{finalResult.total_questions}</p>
                    <p className="text-xs text-muted-foreground mt-1">答对题数</p>
                  </StatCell>
                  <StatCell>
                    <p className="text-2xl font-bold text-primary">+{finalResult.xp_earned}</p>
                    <p className="text-xs text-muted-foreground mt-1">经验值</p>
                  </StatCell>
                  <StatCell>
                    <p className="text-2xl font-bold text-amber-600">+{finalResult.mastery_points_earned}</p>
                    <p className="text-xs text-muted-foreground mt-1">掌握点</p>
                  </StatCell>
                </StatsGrid>

                {finalResult.recommendations.length > 0 && (
                  <div className="p-6 border-t border-border">
                    <p className="font-medium text-foreground mb-2">学习建议</p>
                    <ul className="text-muted-foreground text-sm space-y-1">
                      {finalResult.recommendations.map((rec) => (
                        <li key={rec}>• {rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="p-6 border-t border-border">
                  <Button
                    type="button"
                    onClick={onBackToChapters}
                    className="w-full"
                  >
                    返回章节列表
                  </Button>
                </div>
              </Panel>
            </div>
          </Grid>
        </PageContainer>
      </main>
    </div>
  );
}
