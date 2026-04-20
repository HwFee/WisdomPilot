"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { Lightbulb, Sparkles, BookOpen, Gem, Loader2, X, AlertCircle, GripVertical } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
    const saved = localStorage.getItem('aiHintModalPosition');
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
    localStorage.setItem('aiHintModalPosition', JSON.stringify(pos));
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
      setIsDragging(false);
      if (position) {
        savePosition(position);
      }
      dragStartRef.current = null;
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, position, savePosition]);

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
      className={`
        bg-white rounded-2xl shadow-2xl border border-gray-200
        w-full max-w-lg
        max-h-[80vh]
        overflow-hidden flex flex-col
        ${isDragging ? 'select-none' : ''}
      `}
    >
          {/* 可拖动的标题栏 */}
          <div
            className="flex items-center justify-between p-4 sm:p-5 border-b bg-gradient-to-r from-purple-50 to-blue-50 rounded-t-2xl cursor-grab active:cursor-grabbing"
            onMouseDown={handleMouseDown}
          >
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${config.bgColor}`}>
                <Icon className={`w-5 h-5 ${config.color}`} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  {config.label}
                  {isCached && (
                    <span className="text-xs font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                      已购买
                    </span>
                  )}
                </h3>
                <p className="text-xs text-muted-foreground">{config.description}</p>
              </div>
              {isStreaming && !isCached && (
                <Loader2 className={`w-4 h-4 ${config.color} animate-spin ml-2`} />
              )}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <GripVertical className="w-4 h-4" />
                <span>拖动</span>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-full hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5 text-muted-foreground" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5">
            {hintContent ? (
              <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground/90">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {hintContent}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <div className="relative">
                  <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-purple-500" />
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-white flex items-center justify-center shadow">
                    <Loader2 className="w-3 h-3 text-purple-500 animate-spin" />
                  </div>
                </div>
                <p className="mt-4 text-sm">AI 正在思考...</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 sm:p-5 border-t bg-gray-50/50 rounded-b-2xl">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                {isCached ? (
                  <span className="text-green-600">免费查看（已购买）</span>
                ) : (
                  <>消耗 <Gem className="w-4 h-4 text-purple-500" /> {cost} 智核</>
                )}
              </span>
              <button
                onClick={onClose}
                className="px-5 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-blue-600 transition-all"
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
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCached, setIsCached] = useState(false);  // 是否为缓存内容

  const config = HINT_CONFIG[level];
  const Icon = config.icon;
  const canAfford = currentBalance === undefined || currentBalance >= config.cost;

  const handleClick = async () => {
    setIsOpen(true);
    setHintContent("");
    setIsStreaming(true);
    setError(null);
    setIsCached(false);

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
            setIsCached(true);
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

      // 如果扣费了，刷新余额
      if (!result.cached && result.cost > 0) {
        onBalanceChange();
      }
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
        isCached={isCached}
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
