import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * Skeleton 骨架屏系统
 *
 * 特性：
 * - 基础骨架屏：Skeleton基础组件
 * - 预设模板：CardSkeleton、ListSkeleton、TableSkeleton等
 * - 动画效果：shimmer动画
 */

// 基础骨架屏
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  animate?: boolean
}

function Skeleton({
  className,
  animate = true,
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-md bg-muted",
        animate && "skeleton",
        className
      )}
      {...props}
    />
  )
}

// 文本骨架屏
interface TextSkeletonProps {
  lines?: number
  className?: string
  lineHeight?: 'sm' | 'md' | 'lg'
}

const LINE_HEIGHTS = {
  sm: 'h-3',
  md: 'h-4',
  lg: 'h-5',
}

function TextSkeleton({
  lines = 3,
  className,
  lineHeight = 'md'
}: TextSkeletonProps) {
  return (
    <div className={cn("flex flex-col gap-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={`skeleton-${i}`}
          className={cn(
            LINE_HEIGHTS[lineHeight],
            i === lines - 1 && "w-4/5"
          )}
        />
      ))}
    </div>
  )
}

// 卡片骨架屏
interface CardSkeletonProps {
  showHeader?: boolean
  showImage?: boolean
  lines?: number
  className?: string
}

function CardSkeleton({
  showHeader = true,
  showImage = false,
  lines = 2,
  className,
}: CardSkeletonProps) {
  return (
    <div className={cn("rounded-2xl border border-border bg-card p-5", className)}>
      {showImage && (
        <Skeleton className="w-full aspect-video rounded-xl mb-4" />
      )}
      {showHeader && (
        <div className="flex items-center gap-3 mb-4">
          <Skeleton className="size-10 rounded-xl" />
          <div className="flex-1 gap-y-2">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-3 w-1/4" />
          </div>
        </div>
      )}
      <TextSkeleton lines={lines} />
    </div>
  )
}

// 列表项骨架屏
interface ListItemSkeletonProps {
  showAvatar?: boolean
  lines?: number
  className?: string
}

function ListItemSkeleton({
  showAvatar = true,
  lines = 1,
  className,
}: ListItemSkeletonProps) {
  return (
    <div className={cn("flex items-center gap-3 py-3", className)}>
      {showAvatar && (
        <Skeleton className="size-10 rounded-full flex-shrink-0" />
      )}
      <div className="flex-1 gap-y-2">
        <Skeleton className="h-4 w-1/3" />
        {lines > 1 && <Skeleton className="h-3 w-1/2" />}
      </div>
    </div>
  )
}

// 列表骨架屏
interface ListSkeletonProps {
  items?: number
  showAvatar?: boolean
  className?: string
}

function ListSkeleton({
  items = 5,
  showAvatar = true,
  className,
}: ListSkeletonProps) {
  return (
    <div className={cn("divide-y divide-border", className)}>
      {Array.from({ length: items }).map((_, i) => (
        <ListItemSkeleton key={`skeleton-${i}`} showAvatar={showAvatar} />
      ))}
    </div>
  )
}

// 表格骨架屏
interface TableSkeletonProps {
  rows?: number
  columns?: number
  showHeader?: boolean
  className?: string
}

function TableSkeleton({
  rows = 5,
  columns = 4,
  showHeader = true,
  className,
}: TableSkeletonProps) {
  return (
    <div className={cn("rounded-xl border border-border overflow-hidden", className)}>
      {showHeader && (
        <div className="flex gap-4 p-4 bg-muted/50 border-b border-border">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={`skeleton-${i}`} className="h-4 flex-1" />
          ))}
        </div>
      )}
      <div className="divide-y divide-border">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="flex gap-4 p-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                className={cn(
                  "h-4",
                  colIndex === 0 ? "w-1/4" : "flex-1"
                )}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

// 统计卡片骨架屏
interface StatCardSkeletonProps {
  className?: string
}

function StatCardSkeleton({ className }: StatCardSkeletonProps) {
  return (
    <div className={cn("rounded-2xl border border-border bg-card p-5", className)}>
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="size-10 rounded-xl" />
        <Skeleton className="w-16 h-5 rounded-full" />
      </div>
      <Skeleton className="h-8 w-24 mb-2" />
      <Skeleton className="h-3 w-32" />
    </div>
  )
}

// 用户卡片骨架屏
interface UserCardSkeletonProps {
  className?: string
}

function UserCardSkeleton({ className }: UserCardSkeletonProps) {
  return (
    <div className={cn("flex items-center gap-3 p-4 rounded-xl bg-card border border-border", className)}>
      <Skeleton className="size-12 rounded-full" />
      <div className="flex-1 gap-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-24" />
      </div>
      <Skeleton className="w-20 h-8 rounded-lg" />
    </div>
  )
}

// 课程卡片骨架屏
interface CourseCardSkeletonProps {
  className?: string
}

function CourseCardSkeleton({ className }: CourseCardSkeletonProps) {
  return (
    <div className={cn("rounded-2xl border border-border bg-card overflow-hidden", className)}>
      <Skeleton className="w-full aspect-video" />
      <div className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Skeleton className="size-8 rounded-lg" />
          <Skeleton className="h-4 w-20 rounded-md" />
        </div>
        <Skeleton className="h-5 w-3/4 mb-2" />
        <TextSkeleton lines={2} />
        <div className="flex items-center gap-4 mt-4">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  )
}

// 代码编辑器骨架屏
interface CodeEditorSkeletonProps {
  className?: string
}

function CodeEditorSkeleton({ className }: CodeEditorSkeletonProps) {
  return (
    <div className={cn("rounded-xl border border-border bg-card overflow-hidden", className)}>
      <div className="flex items-center gap-2 p-3 border-b border-border bg-muted/30">
        <Skeleton className="size-3 rounded-full" />
        <Skeleton className="size-3 rounded-full" />
        <Skeleton className="size-3 rounded-full" />
        <Skeleton className="w-32 h-4 ml-4" />
      </div>
      <div className="p-4 flex flex-col gap-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={`skeleton-${i}`} className="flex gap-4">
            <Skeleton className="w-6 h-4" />
            <Skeleton className={cn("h-4", i % 3 === 0 ? "w-3/4" : i % 3 === 1 ? "w-1/2" : "w-2/3")} />
          </div>
        ))}
      </div>
    </div>
  )
}

export {
  Skeleton,
  TextSkeleton,
  CardSkeleton,
  ListItemSkeleton,
  ListSkeleton,
  TableSkeleton,
  StatCardSkeleton,
  UserCardSkeleton,
  CourseCardSkeleton,
  CodeEditorSkeleton,
}
