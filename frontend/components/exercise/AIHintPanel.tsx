"use client";

import { useState } from "react";
import { Lightbulb, Sparkles, BookOpen, Gem, Loader2, X, AlertCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ========================================
// Types
// ========================================

export interface ExerciseHintData {
  exercise_title: string;
  exercise_description: string;
  difficulty: number;
  knowledge_points: string[];
  code_template?: string;
  sample_input?: string;
  sample_output?: string;
}

interface AIHintPanelProps {
  onGetHint: (level: "light" | "medium" | "deep") => Promise<{ hint: string; cost: number } | null>;
  currentBalance?: number;
  disabled?: boolean;
}

// ========================================
// Hint Configuration
// ========================================

const HINT_CONFIG = {
  light: {
    icon: Lightbulb,
    label: "轻度提示",
    description: "思路方向",
    cost: 1,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    hoverColor: "hover:bg-yellow-500/20",
  },
  medium: {
    icon: Sparkles,
    label: "中度提示",
    description: "关键步骤",
    cost: 3,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    hoverColor: "hover:bg-purple-500/20",
  },
  deep: {
    icon: BookOpen,
    label: "深度解析",
    description: "完整解答",
    cost: 5,
    color: "text-blue-600",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    hoverColor: "hover:bg-blue-500/20",
  },
} as const;

// ========================================
// AI Hint Button Component
// ========================================

interface AIHintButtonProps {
  level: "light" | "medium" | "deep";
  onGetHint: (level: "light" | "medium" | "deep") => Promise<{ hint: string; cost: number } | null>;
  disabled?: boolean;
  currentBalance?: number;
}

export function AIHintButton({ level, onGetHint, disabled, currentBalance }: AIHintButtonProps) {
  const [loading, setLoading] = useState(false);
  const [hint, setHint] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const config = HINT_CONFIG[level];
  const Icon = config.icon;
  const canAfford = currentBalance === undefined || currentBalance >= config.cost;

  const handleClick = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await onGetHint(level);
      if (result) {
        setHint(result.hint);
      }
    } catch {
      setError("获取提示失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setHint(null);
    setError(null);
  };

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        disabled={disabled || loading || !canAfford}
        className={`
          flex flex-col items-center gap-1 p-2 rounded-lg border transition-all
          ${config.bgColor} ${config.borderColor} ${config.hoverColor}
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        title={`${config.label}: ${config.description} (-${config.cost}智核)`}
      >
        {loading ? (
          <Loader2 className={`w-5 h-5 ${config.color} animate-spin`} />
        ) : (
          <Icon className={`w-5 h-5 ${config.color}`} />
        )}
        <span className={`text-xs font-medium ${config.color}`}>
          {config.label}
        </span>
        <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
          <Gem className="w-3 h-3" />
          {config.cost}
        </span>
      </button>

      {/* Insufficient balance indicator */}
      {!canAfford && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
          <AlertCircle className="w-2 h-2 text-white" />
        </div>
      )}

      {/* Hint display modal */}
      {hint && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Icon className={`w-6 h-6 ${config.color}`} />
                <h3 className="text-lg font-bold text-foreground">
                  {config.label}
                </h3>
              </div>
              <button
                onClick={handleClose}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {hint}
                </ReactMarkdown>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                消耗 <Gem className="w-3 h-3 inline text-purple-500" /> {config.cost} 智核
              </span>
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
              >
                知道了
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error toast */}
      {error && (
        <div className="fixed bottom-4 right-4 z-50 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-2">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

// ========================================
// AI Hint Panel - 包含三个级别的提示按钮
// ========================================

export function AIHintPanel({ onGetHint, currentBalance, disabled }: AIHintPanelProps) {
  return (
    <div className="bg-card rounded-xl border p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-500" />
          AI 提示
        </h3>
        {currentBalance !== undefined && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Gem className="w-3 h-3 text-purple-500" />
            {currentBalance}
          </span>
        )}
      </div>
      <div className="flex gap-2">
        <AIHintButton
          level="light"
          onGetHint={onGetHint}
          disabled={disabled}
          currentBalance={currentBalance}
        />
        <AIHintButton
          level="medium"
          onGetHint={onGetHint}
          disabled={disabled}
          currentBalance={currentBalance}
        />
        <AIHintButton
          level="deep"
          onGetHint={onGetHint}
          disabled={disabled}
          currentBalance={currentBalance}
        />
      </div>
    </div>
  );
}

// ========================================
// Stream Hint Modal - 流式输出显示
// ========================================

interface StreamHintModalProps {
  isOpen: boolean;
  onClose: () => void;
  level: "light" | "medium" | "deep";
  hintContent: string;
  isStreaming: boolean;
  cost: number;
}

export function StreamHintModal({
  isOpen,
  onClose,
  level,
  hintContent,
  isStreaming,
  cost,
}: StreamHintModalProps) {
  const config = HINT_CONFIG[level];
  const Icon = config.icon;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Icon className={`w-6 h-6 ${config.color}`} />
            <h3 className="text-lg font-bold text-foreground">
              {config.label}
            </h3>
            {isStreaming && (
              <Loader2 className={`w-4 h-4 ${config.color} animate-spin ml-2`} />
            )}
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {hintContent ? (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {hintContent}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              AI 正在思考...
            </div>
          )}
        </div>

        <div className="mt-4 pt-4 border-t flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            消耗 <Gem className="w-3 h-3 inline text-purple-500" /> {cost} 智核
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            {isStreaming ? "关闭" : "知道了"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ========================================
// Stream Hint Button - 支持流式输出的按钮
// ========================================

interface StreamHintButtonProps {
  level: "light" | "medium" | "deep";
  exerciseData: ExerciseHintData;
  token: string;
  onBalanceChange: () => void;  // 余额变化时回调（刷新余额）
  currentBalance?: number;
  disabled?: boolean;
}

export function StreamHintButton({
  level,
  exerciseData,
  token,
  onBalanceChange,
  currentBalance,
  disabled,
}: StreamHintButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hintContent, setHintContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [costDeducted, setCostDeducted] = useState(false);

  const config = HINT_CONFIG[level];
  const Icon = config.icon;
  const canAfford = currentBalance === undefined || currentBalance >= config.cost;

  const handleClick = async () => {
    setIsOpen(true);
    setHintContent("");
    setIsStreaming(true);
    setError(null);
    setCostDeducted(false);

    try {
      // 动态导入 API 函数避免循环依赖
      const { streamExerciseHint } = await import("@/lib/api/ai");

      await streamExerciseHint(
        {
          exercise_title: exerciseData.exercise_title,
          exercise_description: exerciseData.exercise_description,
          difficulty: exerciseData.difficulty,
          knowledge_points: exerciseData.knowledge_points,
          hint_level: level,
          code_template: exerciseData.code_template,
          sample_input: exerciseData.sample_input,
          sample_output: exerciseData.sample_output,
        },
        token,
        (chunk) => {
          setHintContent((prev) => prev + chunk);
          // 第一个 chunk 到达时标记已扣费
          if (!costDeducted) {
            setCostDeducted(true);
            onBalanceChange();
          }
        },
        (errorMsg) => {
          // 如果是余额不足错误，刷新余额
          if (errorMsg.includes("余额不足") || errorMsg.includes("INSUFFICIENT")) {
            onBalanceChange();
          }
          setError(errorMsg);
          setIsStreaming(false);
        },
        () => {
          setIsStreaming(false);
        }
      );
    } catch {
      setError("AI 提示请求失败，请重试");
      setIsStreaming(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setHintContent("");
    setIsStreaming(false);
    setError(null);
  };

  return (
    <>
      <div className="relative">
        <button
          onClick={handleClick}
          disabled={disabled || !canAfford}
          className={`
            flex flex-col items-center gap-1 p-2 rounded-lg border transition-all
            ${config.bgColor} ${config.borderColor} ${config.hoverColor}
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          title={`${config.label}: ${config.description} (-${config.cost}智核)`}
        >
          <Icon className={`w-5 h-5 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>
            {config.label}
          </span>
          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
            <Gem className="w-3 h-3" />
            {config.cost}
          </span>
        </button>

        {/* Insufficient balance indicator */}
        {!canAfford && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
            <AlertCircle className="w-2 h-2 text-white" />
          </div>
        )}
      </div>

      {/* Stream Modal */}
      <StreamHintModal
        isOpen={isOpen}
        onClose={handleClose}
        level={level}
        hintContent={hintContent}
        isStreaming={isStreaming}
        cost={config.cost}
      />

      {/* Error toast */}
      {error && (
        <div className="fixed bottom-4 right-4 z-50 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-2">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </>
  );
}

// ========================================
// Stream Hint Panel - 包含三个流式提示按钮
// ========================================

interface StreamHintPanelProps {
  exerciseData: ExerciseHintData;
  token: string;
  onBalanceChange: () => void;  // 余额变化时回调（刷新余额）
  currentBalance?: number;
  disabled?: boolean;
}

export function StreamHintPanel({
  exerciseData,
  token,
  onBalanceChange,
  currentBalance,
  disabled,
}: StreamHintPanelProps) {
  return (
    <div className="bg-card rounded-xl border p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-500" />
          AI 提示
        </h3>
        {currentBalance !== undefined && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Gem className="w-3 h-3 text-purple-500" />
            {currentBalance}
          </span>
        )}
      </div>
      <div className="flex gap-2">
        <StreamHintButton
          level="light"
          exerciseData={exerciseData}
          token={token}
          onBalanceChange={onBalanceChange}
          disabled={disabled}
          currentBalance={currentBalance}
        />
        <StreamHintButton
          level="medium"
          exerciseData={exerciseData}
          token={token}
          onBalanceChange={onBalanceChange}
          disabled={disabled}
          currentBalance={currentBalance}
        />
        <StreamHintButton
          level="deep"
          exerciseData={exerciseData}
          token={token}
          onBalanceChange={onBalanceChange}
          disabled={disabled}
          currentBalance={currentBalance}
        />
      </div>
    </div>
  );
}
