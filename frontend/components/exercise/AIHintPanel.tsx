"use client";

import { useState, useEffect, useCallback, useRef, useEffectEvent } from "react";
import { createPortal } from "react-dom";
import { Lightbulb, Sparkles, BookOpen, Gem, Loader2, X, AlertCircle, GripVertical } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";
import { cn } from "@/lib/utils";

// ========================================
// Types
// ========================================

export interface ExerciseHintData {
  exercise_id?: string;  // 题目唯一标识
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

  const fetchHint = async () => {
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
      <button type="button"
        onClick={fetchHint}
        disabled={disabled || loading || !canAfford}
        className={`
          flex flex-col items-center gap-1 p-2 rounded-lg border transition-all
          ${config.bgColor} ${config.borderColor} ${config.hoverColor}
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        title={`${config.label}: ${config.description} (-${config.cost}智核)`}
      >
        {loading ? (
          <Loader2 className={`size-5 ${config.color} animate-spin`} />
        ) : (
          <Icon className={`size-5 ${config.color}`} />
        )}
        <span className={`text-xs font-medium ${config.color}`}>
          {config.label}
        </span>
        <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
          <Gem className="size-3" />
          {config.cost}
        </span>
      </button>

      {/* Insufficient balance indicator */}
      {!canAfford && (
        <div className="absolute -top-1 -right-1 size-3 bg-red-500 rounded-full flex items-center justify-center">
          <AlertCircle className="size-2 text-white" />
        </div>
      )}

      {/* Hint display modal */}
      {hint && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xl">
          <div className="relative w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col rounded-2xl border border-white/10 shadow-2xl bg-card/95 backdrop-blur-sm animate-modal-enter"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            tabIndex={-1}
          >
            {/* 顶部光效 */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-border/50 bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${config.bgColor}`}>
                  <Icon className={`size-5 ${config.color}`} />
                </div>
                <h3 className="text-lg font-semibold text-foreground">
                  {config.label}
                </h3>
              </div>
              <button type="button"
                onClick={handleClose}
                className="p-1.5 rounded-lg bg-muted/50 hover:bg-muted border border-border/50 hover:border-border transition-all group"
              >
                <X className="size-4 text-muted-foreground group-hover:text-foreground transition-colors" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              <div className="text-muted-foreground leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                  components={{
                    h1: ({ children }) => <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mt-3 mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-medium text-foreground mt-2 mb-1">{children}</h3>,
                    p: ({ children }) => <p className="mb-2 last:mb-0 text-muted-foreground">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>,
                    li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/30 pl-4 italic my-2 text-muted-foreground">{children}</blockquote>,
                    strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                    code({ className, children, ...props }) {
                      const isInline = !className
                      if (isInline) {
                        return (
<code className="bg-muted text-foreground px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                            {children}
                          </code>
                        )
                      }
                      return <code className={className} {...props}>{children}</code>
                    },
                    pre({ children }) {
                      return (
                        <pre
                          className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3"
                          style={{ backgroundColor: '#1e293b', color: '#e2e8f0', border: '1px solid #334155' }}
                        >
                          {children}
                        </pre>
                      )
                    },
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-3">
                        <table className="min-w-full border-collapse border border-border">{children}</table>
                      </div>
                    ),
                    thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                    th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground border border-border">{children}</th>,
                    td: ({ children }) => <td className="px-3 py-2 text-sm text-muted-foreground border border-border">{children}</td>,
                  }}
                >
                  {hint}
                </ReactMarkdown>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-border/50 bg-muted/30 flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Gem className="size-3 text-purple-500" />
                消耗 {config.cost} 智核
              </span>
              <button type="button"
                onClick={handleClose}
                className="px-5 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-primary to-primary-600 text-primary-foreground hover:from-primary-600 hover:to-primary-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
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
          <AlertCircle className="size-4" />
          {error}
          <button type="button" onClick={() => setError(null)} className="ml-2">
            <X className="size-4" />
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
          <Sparkles className="size-4 text-purple-500" />
          AI 提示
        </h3>
        {currentBalance !== undefined && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Gem className="size-3 text-purple-500" />
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
  isCached?: boolean;  // 是否为缓存内容
}

export function StreamHintModal({
  isOpen,
  onClose,
  level,
  hintContent,
  isStreaming,
  cost,
  isCached = false,
}: StreamHintModalProps) {
  const config = HINT_CONFIG[level];
  const Icon = config.icon;

  // 拖动相关状态
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ x: number; y: number; posX: number; posY: number } | null>(null);

  // 从 localStorage 加载保存的位置
  useEffect(() => {
    const saved = localStorage.getItem('aiHintModalPosition:v1');
    if (saved) {
      try {
        setPosition(JSON.parse(saved));
      } catch {
        // 解析失败，使用默认位置
      }
    }
  }, []);

  // 保存位置到 localStorage
  const savePosition = useCallback((pos: { x: number; y: number }) => {
    localStorage.setItem('aiHintModalPosition:v1', JSON.stringify(pos));
  }, []);

  // 拖动开始
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    const currentPos = position || { x: 0, y: 0 };
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      posX: currentPos.x,
      posY: currentPos.y,
    };
    e.preventDefault();
  };

  // 拖动中
  const handleDragEnd = useEffectEvent(() => {
    setIsDragging(false);
    if (position) {
      savePosition(position);
    }
    dragStartRef.current = null;
  });

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!dragStartRef.current) return;

      const deltaX = e.clientX - dragStartRef.current.x;
      const deltaY = e.clientY - dragStartRef.current.y;

      const newPos = {
        x: dragStartRef.current.posX + deltaX,
        y: dragStartRef.current.posY + deltaY,
      };

      setPosition(newPos);
    };

    const handleMouseUp = () => {
      handleDragEnd();
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  if (!isOpen) return null;

  // 计算样式 - 始终使用 fixed 定位
  const modalStyle: React.CSSProperties = {
    position: 'fixed',
    left: position ? `calc(50% + ${position.x}px)` : '50%',
    top: position ? `calc(50% + ${position.y}px)` : '50%',
    transform: 'translate(-50%, -50%)',
    zIndex: 9999,
  };

  // 模态框内容 - 不使用 backdrop，允许用户继续操作页面
  const modalContent = (
    <div
      style={modalStyle}
      className={cn(
        "w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col rounded-2xl",
        "bg-card/95 backdrop-blur-sm border border-white/10 shadow-2xl",
        isDragging ? 'select-none' : ''
      )}
    >
      {/* 顶部光效 */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent z-10" />

      {/* 可拖动的标题栏 */}
      <div
        className="flex items-center justify-between px-5 py-4 border-b border-border/50 bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent rounded-t-2xl cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        role="button"
        tabIndex={0}
        aria-label="拖动"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`size-5 ${config.color}`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
              {config.label}
              {isCached && (
                <span className="text-xs font-normal text-green-600 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                  已购买
                </span>
              )}
            </h3>
            <p className="text-xs text-muted-foreground">{config.description}</p>
          </div>
          {isStreaming && !isCached && (
            <Loader2 className={`size-4 ${config.color} animate-spin ml-2`} />
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <GripVertical className="size-4" />
            <span>拖动</span>
          </div>
          <button type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg bg-muted/50 hover:bg-muted border border-border/50 hover:border-border transition-all group"
          >
            <X className="size-4 text-muted-foreground group-hover:text-foreground transition-colors" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {hintContent ? (
          <div className="text-muted-foreground leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex, rehypeHighlight]}
              components={{
                h1: ({ children }) => <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mt-3 mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-base font-medium text-foreground mt-2 mb-1">{children}</h3>,
                p: ({ children }) => <p className="mb-2 last:mb-0 text-muted-foreground">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>,
                li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
                blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/30 pl-4 italic my-2 text-muted-foreground">{children}</blockquote>,
                strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                code({ className, children, ...props }) {
                  const isInline = !className
                  if (isInline) {
                    return (
                      <code className="bg-muted text-foreground px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                        {children}
                      </code>
                    )
                  }
                  return <code className={className} {...props}>{children}</code>
                },
pre({ children }) {
                   return (
                     <pre
                       className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3"
                       style={{ backgroundColor: '#1e293b', color: '#e2e8f0', border: '1px solid #334155' }}
                     >
                       {children}
                     </pre>
                   )
                 },
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3">
                    <table className="min-w-full border-collapse border border-border">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground border border-border">{children}</th>,
                td: ({ children }) => <td className="px-3 py-2 text-sm text-muted-foreground border border-border">{children}</td>,
              }}
            >
              {hintContent}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <div className="relative">
              <div className="size-12 rounded-full bg-purple-500/10 flex items-center justify-center">
                <Sparkles className="size-6 text-purple-500" />
              </div>
              <div className="absolute -bottom-1 -right-1 size-5 rounded-full bg-card flex items-center justify-center shadow border border-border/50">
                <Loader2 className="size-3 text-purple-500 animate-spin" />
              </div>
            </div>
            <p className="mt-4 text-sm">AI 正在思考...</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border/50 bg-muted/30 rounded-b-2xl">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground flex items-center gap-1">
            {isCached ? (
              <span className="text-green-600">免费查看（已购买）</span>
            ) : (
              <>消耗 <Gem className="size-4 text-purple-500" /> {cost} 智核</>
            )}
          </span>
          <button type="button"
            onClick={onClose}
            className="px-5 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-primary to-primary-600 text-primary-foreground hover:from-primary-600 hover:to-primary-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
          >
            {isStreaming && !isCached ? "关闭" : "知道了"}
          </button>
        </div>
      </div>
    </div>
  );

  // 使用 Portal 渲染到 body，避免被父容器 CSS 影响
  return createPortal(modalContent, document.body);
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
  const [streamState, setStreamState] = useState({ streaming: false, cached: false });
  const { streaming: isStreaming, cached: isCached } = streamState;
  const [error, setError] = useState<string | null>(null);

  const config = HINT_CONFIG[level];
  const Icon = config.icon;
  const canAfford = currentBalance === undefined || currentBalance >= config.cost;

  const fetchStreamHint = async () => {
    setIsOpen(true);
    setHintContent("");
    setStreamState({ streaming: true, cached: false });
    setError(null);

    try {
      // 动态导入 API 函数避免循环依赖
      const { streamExerciseHint } = await import("@/lib/api/ai");

      let wasCached = false;

      const result = await streamExerciseHint(
        {
          exercise_id: exerciseData.exercise_id,  // 传递题目 ID
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
        (chunk, cached) => {
          setHintContent((prev) => prev + chunk);
          if (cached) {
            wasCached = true;
            setStreamState(prev => ({ ...prev, cached: true }));
          }
        },
        (errorMsg) => {
          // 如果是余额不足错误，刷新余额
          if (errorMsg.includes("余额不足") || errorMsg.includes("INSUFFICIENT")) {
            onBalanceChange();
          }
          setError(errorMsg);
          setStreamState(prev => ({ ...prev, streaming: false }));
        },
        () => {
          setStreamState(prev => ({ ...prev, streaming: false }));
        }
      );

      // 如果扣费了，刷新余额
      if (!result.cached && result.cost > 0) {
        onBalanceChange();
      }
    } catch {
      setError("AI 提示请求失败，请重试");
      setStreamState(prev => ({ ...prev, streaming: false }));
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setHintContent("");
    setStreamState({ streaming: false, cached: false });
    setError(null);
  };

  return (
    <>
      <div className="relative">
        <button type="button"
          onClick={fetchStreamHint}
          disabled={disabled || !canAfford}
          className={`
            flex flex-col items-center gap-1 p-2 rounded-lg border transition-all
            ${config.bgColor} ${config.borderColor} ${config.hoverColor}
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          title={`${config.label}: ${config.description} (-${config.cost}智核)`}
        >
          <Icon className={`size-5 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>
            {config.label}
          </span>
          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
            <Gem className="size-3" />
            {config.cost}
          </span>
        </button>

        {/* Insufficient balance indicator */}
        {!canAfford && (
          <div className="absolute -top-1 -right-1 size-3 bg-red-500 rounded-full flex items-center justify-center">
            <AlertCircle className="size-2 text-white" />
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
        isCached={isCached}
      />

      {/* Error toast */}
      {error && (
        <div className="fixed bottom-4 right-4 z-50 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <AlertCircle className="size-4" />
          {error}
          <button type="button" onClick={() => setError(null)} className="ml-2">
            <X className="size-4" />
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
          <Sparkles className="size-4 text-purple-500" />
          AI 提示
        </h3>
        {currentBalance !== undefined && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Gem className="size-3 text-purple-500" />
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
