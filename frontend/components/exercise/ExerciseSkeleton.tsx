/**
 * ExerciseSkeleton - 题目骨架屏占位组件
 * Swiss style: uses design tokens, no custom CSS classes.
 */
interface ExerciseSkeletonProps {
  index?: number
  showNumber?: boolean
}

export function ExerciseSkeleton({ index = 0, showNumber = true }: ExerciseSkeletonProps) {
  return (
    <div className="animate-pulse p-4 border border-border rounded-lg">
      {showNumber && <div className="h-3 w-8 bg-muted rounded mb-3" />}
      <div className="h-4 bg-muted rounded w-3/4 mb-2" />
      <div className="h-4 bg-muted rounded w-1/2" />
    </div>
  )
}

/**
 * ExerciseSkeletonList - 多个骨架屏占位
 */
interface ExerciseSkeletonListProps {
  count: number
  startIndex?: number
}

function ExerciseSkeletonList({ count, startIndex = 0 }: ExerciseSkeletonListProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <ExerciseSkeleton key={startIndex + i} index={startIndex + i} />
      ))}
    </div>
  )
}

/**
 * GeneratingIndicator - AI 生成中的占位指示
 * Swiss style: tokenized colors, no custom animation styles.
 */
export function GeneratingIndicator() {
  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <span
        className="h-2 w-2 rounded-full bg-primary animate-pulse"
        style={{ animationDelay: '0ms' }}
      />
      <span
        className="h-2 w-2 rounded-full bg-primary animate-pulse"
        style={{ animationDelay: '200ms' }}
      />
      <span
        className="h-2 w-2 rounded-full bg-primary animate-pulse"
        style={{ animationDelay: '400ms' }}
      />
      <span className="text-sm">AI 正在生成...</span>
    </div>
  )
}
