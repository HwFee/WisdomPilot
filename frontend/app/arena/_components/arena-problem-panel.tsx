"use client";

import { Loader2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import "katex/dist/katex.min.css";
import { SampleIOCard } from "@/components/exercise/SampleIOCard";
import { StreamHintPanel } from "@/components/exercise/AIHintPanel";
import { getStoredToken } from "@/lib/api";
import type { Exercise } from "../types";

type SetCoreBalance = React.Dispatch<React.SetStateAction<number | undefined>>;

export interface ArenaProblemPanelProps {
  currentExercise: Exercise | undefined;
  currentIndex: number;
  contentLoadingMap: Record<number, boolean>;
  contentErrorMap: Record<number, string>;
  language: string;
  loadExerciseContent: (
    exerciseId: number,
    index: number,
    language: string,
  ) => Promise<void>;
  isCustomRunning: boolean;
  handleSampleRun: (input: string, expectedOutput?: string) => Promise<void>;
  coreBalance: number | undefined;
  setCoreBalance: SetCoreBalance;
  isSubmitting: boolean;
}

export function ArenaProblemPanel({
  currentExercise,
  currentIndex,
  contentLoadingMap,
  contentErrorMap,
  language,
  loadExerciseContent,
  isCustomRunning,
  handleSampleRun,
  coreBalance,
  setCoreBalance,
  isSubmitting,
}: ArenaProblemPanelProps) {
  if (!currentExercise) return null;

  return (
    <div className="p-6">
      {contentLoadingMap[currentExercise.id] ? (
        <div className="mb-6 p-4 bg-secondary rounded-lg">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" strokeWidth={1.5} />
            正在加载题面...
          </div>
        </div>
      ) : contentErrorMap[currentExercise.id] ? (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-red-600 mb-2">
            <AlertTriangle className="size-4" strokeWidth={1.5} />
            题面加载失败
          </div>
          <p className="text-xs text-red-600 mb-3">{contentErrorMap[currentExercise.id]}</p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => loadExerciseContent(currentExercise.id, currentIndex, language)}
            className="border-red-500 text-red-600 hover:bg-red-50"
          >
            重试
          </Button>
        </div>
      ) : currentExercise.content.description ? (
        <div className="text-muted-foreground leading-relaxed mb-6">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={{
              h1: ({ children }) => <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>,
              h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mt-4 mb-2 border-b border-border pb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-base font-semibold text-foreground mt-3 mb-2">{children}</h3>,
              p: ({ children }) => <p className="text-muted-foreground mb-2 leading-relaxed">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>,
              li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
              blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/20 pl-4 italic my-2 text-muted-foreground">{children}</blockquote>,
              strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code className="bg-secondary px-1.5 py-0.5 rounded text-sm text-red-600 font-mono border border-border" {...props}>
                    {children}
                  </code>
                ) : (
                  <code className={className} {...props}>{children}</code>
                );
              },
              pre: ({ children }) => (
                <pre
                  className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3 bg-slate-900 text-slate-100 border border-slate-700"
                >
                  {children}
                </pre>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-3">
                  <table className="min-w-full border-collapse border border-border">{children}</table>
                </div>
              ),
              thead: ({ children }) => <thead className="bg-secondary">{children}</thead>,
              th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground border border-border">{children}</th>,
              td: ({ children }) => <td className="px-3 py-2 text-sm text-muted-foreground border border-border">{children}</td>,
            }}
          >
            {currentExercise.content.description}
          </ReactMarkdown>
        </div>
      ) : null}

      {/* Sample I/O */}
      {currentExercise.content.samples &&
      currentExercise.content.samples.length > 0 ? (
        <div className="mb-6">
          <SampleIOCard
            input={currentExercise.content.samples[0].input}
            output={currentExercise.content.samples[0].output}
            onRun={(input) =>
              handleSampleRun(
                input,
                currentExercise.content.samples![0].output,
              )
            }
            isRunning={isCustomRunning}
          />
        </div>
      ) : currentExercise.content.sample_input ||
        currentExercise.content.sample_output ? (
        <div className="mb-6">
          <SampleIOCard
            input={currentExercise.content.sample_input || ""}
            output={currentExercise.content.sample_output || ""}
            onRun={(input) =>
              handleSampleRun(
                input,
                currentExercise.content.sample_output,
              )
            }
            isRunning={isCustomRunning}
          />
        </div>
      ) : null}

      {currentExercise.knowledge_points.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {currentExercise.knowledge_points.map((kp) => (
            <span
              key={`arena-${currentExercise.id}-${kp}`}
              className="knowledge-tag px-3 py-1.5 text-primary text-xs rounded-lg font-medium"
            >
              {kp}
            </span>
          ))}
        </div>
      )}

      {/* AI Hint Panel */}
      <div className="mt-6">
        <StreamHintPanel
          exerciseData={{
            exercise_id: String(currentExercise.id),
            exercise_title: currentExercise.content.title || `题目 #${currentExercise.id}`,
            exercise_description: currentExercise.content.description || currentExercise.content.text || "",
            difficulty: currentExercise.difficulty,
            knowledge_points: currentExercise.knowledge_points || [],
            code_template: currentExercise.content.code_template,
            sample_input: currentExercise.content.sample_input,
            sample_output: currentExercise.content.sample_output,
          }}
          token={getStoredToken() || ""}
          onBalanceChange={async () => {
            const token = getStoredToken();
            if (token) {
              try {
                const { getCoreBalance } = await import("@/lib/api/core");
                const balanceData = await getCoreBalance();
                setCoreBalance(balanceData.balance);
              } catch {
                // 忽略刷新失败
              }
            }
          }}
          currentBalance={coreBalance}
          disabled={isSubmitting}
        />
      </div>
    </div>
  );
}
