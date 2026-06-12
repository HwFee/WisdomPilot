"use client";

import {
  CheckCircle,
  XCircle,
  ArrowRight,
  RotateCcw,
  Zap,
  Loader2,
  Send,
  Star,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { LuoguTestCasesSummary } from "@/components/exercise/LuoguTestCaseTable";
import { TIER_COLORS } from "@/lib/api";
import type { FeedbackState, TestCaseResult } from "../types";

type TierInfo = {
  tier: string;
  sub_tier: number;
  stars: number;
  full_name: string;
} | null;

export interface ArenaBottomBarProps {
  feedbackState: FeedbackState;
  tierInfo: TierInfo | null;
  testResults: TestCaseResult[];
  isSubmitting: boolean;
  canGoNext: boolean;
  onSubmit: () => void;
  onRetry: () => void;
  onNext: () => void;
  onShowOutput: () => void;
}

const FOOTER_STYLES: Record<FeedbackState, string> = {
  idle: "bg-card border-t border-border",
  correct: "bg-emerald-50 border-t-2 border-emerald-500",
  wrong: "bg-red-50 border-t-2 border-red-500",
};

export function ArenaBottomBar({
  feedbackState,
  tierInfo,
  testResults,
  isSubmitting,
  canGoNext,
  onSubmit,
  onRetry,
  onNext,
  onShowOutput,
}: ArenaBottomBarProps) {
  return (
    <footer className={cn(FOOTER_STYLES[feedbackState])}>
      <div className="px-6 py-4">
        {feedbackState === "idle" ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-primary-50 rounded-lg flex items-center justify-center border border-primary/20">
                  <Zap className="size-5 text-amber-600" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm text-foreground font-medium">
                    挑战之路
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {tierInfo ? (
                      <>
                        当前段位{" "}
                        <span className="font-medium" style={{ color: TIER_COLORS[tierInfo.tier as keyof typeof TIER_COLORS] || '#CD7F32' }}>
                          {tierInfo.full_name}
                        </span>
                        {" "}<span className="text-amber-600 flex items-center inline-flex"><Star className="size-3.5 fill-amber-500" strokeWidth={1.5} />{tierInfo.stars}</span>
                      </>
                    ) : (
                      "加载中..."
                    )}
                  </p>
                </div>
              </div>

              {testResults.length > 0 && (
                <>
                  <div className="h-6 w-px bg-border" />
                  <LuoguTestCasesSummary
                    passedCount={testResults.filter((r) => r.passed).length}
                    totalCount={testResults.length}
                  />
                </>
              )}
            </div>

            <div className="action-buttons-group">
              <Button
                type="button"
                onClick={onSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="size-4 mr-2 animate-spin" strokeWidth={1.5} />
                    提交中...
                  </>
                ) : (
                  <>
                    <Send className="size-4 mr-2" strokeWidth={1.5} />
                    提交
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : feedbackState === "correct" ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="size-10 bg-emerald-50 rounded-lg flex items-center justify-center border border-emerald-500">
                <CheckCircle className="size-6 text-emerald-600" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-semibold text-emerald-600">
                  太棒了！全部通过
                </p>
                <p className="text-sm text-emerald-600/70">继续挑战下一题</p>
              </div>
            </div>
            <div className="action-buttons-group">
              <Button
                type="button"
                variant="outline"
                onClick={onRetry}
              >
                <RotateCcw className="size-4 mr-2" strokeWidth={1.5} />
                重新作答
              </Button>
              {canGoNext && (
                <Button
                  type="button"
                  onClick={onNext}
                >
                  下一题
                  <ArrowRight className="size-4 ml-2" strokeWidth={1.5} />
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="size-10 bg-red-50 rounded-lg flex items-center justify-center border border-red-500">
                <XCircle className="size-6 text-red-600" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-semibold text-red-600">答案错误</p>
                {testResults.length > 0 && (
                  <p className="text-sm text-red-600/70">
                    通过 {testResults.filter((r) => r.passed).length}/{testResults.length} 个测试点 ·
                    修改后重新提交
                  </p>
                )}
              </div>
            </div>
            <div className="action-buttons-group">
              <Button
                type="button"
                variant="outline"
                onClick={onRetry}
              >
                <RotateCcw className="size-4 mr-2" strokeWidth={1.5} />
                重新作答
              </Button>
              {testResults.length > 0 && (
                <Button
                  type="button"
                  onClick={onShowOutput}
                >
                  查看详情
                </Button>
              )}
              {canGoNext && (
                <Button
                  type="button"
                  onClick={onNext}
                >
                  下一题
                  <ArrowRight className="size-4 ml-2" strokeWidth={1.5} />
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </footer>
  );
}
