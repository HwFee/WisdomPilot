"use client";

/**
 * ExerciseSkeleton - 题目骨架屏占位组件
 *
 * 用于流式生成模式，在题目生成过程中显示占位动画
 */

import { motion } from "framer-motion";

interface ExerciseSkeletonProps {
  index?: number;
  showNumber?: boolean;
}

export function ExerciseSkeleton({ index = 0, showNumber = true }: ExerciseSkeletonProps) {
  return (
    <div className="bg-card rounded-2xl border border-border/50 p-6 mb-4 animate-pulse">
      {/* 题目序号和类型标签 */}
      <div className="flex items-center gap-3 mb-4">
        {showNumber && (
          <div className="w-8 h-8 bg-muted rounded-lg" />
        )}
        <div className="w-16 h-6 bg-muted rounded-lg" />
        <div className="w-24 h-4 bg-muted rounded-full" />
      </div>

      {/* 题目文本 */}
      <div className="space-y-2 mb-6">
        <div className="h-5 bg-muted rounded w-full" />
        <div className="h-5 bg-muted rounded w-4/5" />
        <div className="h-5 bg-muted rounded w-3/5" />
      </div>

      {/* 选项骨架 */}
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-3 p-3 bg-muted/50 rounded-xl">
            <div className="w-8 h-8 bg-muted rounded-lg flex-shrink-0" />
            <div className="flex-1 h-4 bg-muted rounded" />
          </div>
        ))}
      </div>

      {/* 知识点标签 */}
      <div className="flex gap-2 mt-4 pt-4 border-t border-border/30">
        <div className="w-16 h-5 bg-muted rounded-full" />
        <div className="w-20 h-5 bg-muted rounded-full" />
      </div>
    </div>
  );
}

/**
 * ExerciseSkeletonList - 多个骨架屏占位
 */
interface ExerciseSkeletonListProps {
  count: number;
  startIndex?: number;
}

export function ExerciseSkeletonList({ count, startIndex = 0 }: ExerciseSkeletonListProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <ExerciseSkeleton key={startIndex + i} index={startIndex + i} />
      ))}
    </div>
  );
}

/**
 * GeneratingIndicator - 生成中指示器
 */
export function GeneratingIndicator({ progress, total }: { progress: number; total: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 px-4 py-3 bg-amber-500/10 border border-amber-500/20 rounded-xl mb-4"
    >
      <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      <div className="flex-1">
        <p className="text-sm font-medium text-amber-600">
          题目生成中...
        </p>
        <div className="mt-1 h-1.5 bg-amber-200 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-amber-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${(progress / total) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>
      <span className="text-sm text-amber-600 font-medium">
        {progress}/{total}
      </span>
    </motion.div>
  );
}

export default ExerciseSkeleton;
