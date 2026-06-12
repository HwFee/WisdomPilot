"use client";

import { ArrowLeft, Target, Zap, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { BaseAnswersSubmitResponse } from "@/types/api";
import { PageContainer, Grid, Panel, PanelHeader, StatsGrid, StatCell } from "@/components/layout";

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
  const wrongCount = baseResult.total_questions - baseResult.correct_answers;

  return (
    <div className="min-h-screen bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
        <PageContainer className="h-14 flex items-center justify-between">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onViewQuestions}
          >
            <ArrowLeft className="size-4 mr-2" strokeWidth={1.5} />
            查看题目
          </Button>
          <div className="flex items-center gap-2">
            <Target className="size-5 text-amber-600" strokeWidth={1.5} />
            <span className="font-semibold">学习分析</span>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onBackToChapters}
          >
            退出
          </Button>
        </PageContainer>
      </header>

      <main className="pt-24 pb-12">
        <PageContainer>
          <Grid>
            <div className="col-span-12 lg:col-span-6 lg:col-start-4 space-y-6">
              {/* Summary */}
              <Panel>
                <div className="p-8 text-center border-b border-border">
                  <p className="text-4xl font-bold text-foreground mb-2">
                    {accuracy}%
                  </p>
                  <p className="text-muted-foreground">基础测试正确率</p>
                </div>
                <StatsGrid>
                  <StatCell>
                    <p className="text-2xl font-bold text-emerald-600">{baseResult.correct_answers}</p>
                    <p className="text-xs text-muted-foreground mt-1">正确</p>
                  </StatCell>
                  <StatCell>
                    <p className="text-2xl font-bold text-red-600">{wrongCount}</p>
                    <p className="text-xs text-muted-foreground mt-1">错误</p>
                  </StatCell>
                  <StatCell>
                    <p className="text-2xl font-bold text-foreground">{baseResult.total_questions}</p>
                    <p className="text-xs text-muted-foreground mt-1">总题数</p>
                  </StatCell>
                  <StatCell>
                    <p className="text-2xl font-bold text-foreground">{accuracy}%</p>
                    <p className="text-xs text-muted-foreground mt-1">正确率</p>
                  </StatCell>
                </StatsGrid>
              </Panel>

              {/* Weak points */}
              {baseResult.weak_points.length > 0 && (
                <Panel>
                  <PanelHeader title="需要强化的知识点" />
                  <div className="p-6 flex flex-wrap gap-2">
                    {baseResult.weak_points.map((point) => (
                      <span
                        key={point}
                        className="px-3 py-1 bg-secondary text-amber-600 rounded-lg text-sm"
                      >
                        {point}
                      </span>
                    ))}
                  </div>
                </Panel>
              )}

              {/* Strong points */}
              {baseResult.strong_points.length > 0 && (
                <Panel>
                  <PanelHeader title="已掌握的知识点" />
                  <div className="p-6 flex flex-wrap gap-2">
                    {baseResult.strong_points.map((point) => (
                      <span
                        key={point}
                        className="px-3 py-1 bg-secondary text-emerald-600 rounded-lg text-sm"
                      >
                        {point}
                      </span>
                    ))}
                  </div>
                </Panel>
              )}

              {/* Actions */}
              <Button
                type="button"
                size="lg"
                onClick={onStartEnhancedQuiz}
                disabled={enhancedLoading}
                className="w-full"
              >
                {enhancedLoading ? (
                  <>
                    <Loader2 className="size-5 mr-2 animate-spin" strokeWidth={1.5} />
                    生成强化测试...
                  </>
                ) : (
                  <>
                    <Zap className="size-5 mr-2" strokeWidth={1.5} />
                    开始强化测试
                  </>
                )}
              </Button>

              <Button
                type="button"
                variant="outline"
                size="lg"
                onClick={onBackToChapters}
                className="w-full"
              >
                暂时跳过，返回章节
              </Button>
            </div>
          </Grid>
        </PageContainer>
      </main>
    </div>
  );
}
