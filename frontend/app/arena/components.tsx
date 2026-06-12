import {
  X,
  CheckCircle,
  XCircle,
  ArrowRight,
  Star,
  PartyPopper,
  Frown,
  Lock,
  Trophy,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/layout";
import type { ExerciseProgress } from "./types";

// ========================================
// Constants
// ========================================

const NAV_MAX_VISIBLE = 5;
const NAV_CENTER_INDEX = 2;

// Mirrors backend/app/core/tier_config.py: stars_per_tier for each rank.
const TIER_STARS_CONFIG: Record<string, { name: string; starsNeeded: number }> = {
  bronze: { name: "青铜", starsNeeded: 3 },
  silver: { name: "白银", starsNeeded: 3 },
  gold: { name: "黄金", starsNeeded: 4 },
  platinum: { name: "铂金", starsNeeded: 4 },
  diamond: { name: "钻石", starsNeeded: 5 },
  master: { name: "星耀", starsNeeded: 5 },
  king: { name: "王者", starsNeeded: 0 },
};

// ========================================
// Tier Progress Bar Component
// ========================================

interface TierProgressBarProps {
  tier: string;
  subTier: number;
  stars: number;
  fullName: string;
}

export function TierProgressBar({ tier, subTier, stars, fullName }: TierProgressBarProps) {
  const config = TIER_STARS_CONFIG[tier] || { name: fullName || "未知", starsNeeded: 3 };
  const isKing = tier === "king";
  const starsNeeded = isKing ? Math.max(stars, 1) : config.starsNeeded;
  const progress = isKing ? 100 : Math.min(100, Math.max(0, (stars / starsNeeded) * 100));

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-card border-b border-border">
      <div className="flex items-center gap-2 shrink-0">
        <Trophy className="size-4 text-muted-foreground" strokeWidth={1.5} />
        <span className="text-xs font-medium text-foreground">{fullName || config.name}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <Star className="size-3.5 fill-amber-500 text-amber-500" strokeWidth={1.5} />
        <span className="text-xs font-medium text-foreground">
          {stars}
          {!isKing && <span className="text-muted-foreground">/{starsNeeded}</span>}
        </span>
      </div>
    </div>
  );
}

// ========================================
// Result Modal Component
// ========================================

interface ResultModalProps {
  isCorrect: boolean;
  passedCount: number;
  totalCount: number;
  starsEarned: number;
  promoted: boolean;
  demoted: boolean;
  firstTimeCorrect: boolean;
  firstTimeWrong: boolean;
  onStay: () => void;
  onNext: () => void;
  canGoNext: boolean;
}

export function ResultModal({
  isCorrect,
  passedCount,
  totalCount,
  starsEarned,
  promoted,
  demoted,
  firstTimeCorrect,
  firstTimeWrong,
  onStay,
  onNext,
  canGoNext,
}: ResultModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Panel
        className={`relative max-w-md w-full mx-4 rounded-lg overflow-hidden border-t-4 ${
          isCorrect ? "border-t-emerald-500" : "border-t-red-500"
        }`}
      >
        <div className="p-8">
          <div className="text-center">
            {isCorrect ? (
              <>
                <CheckCircle className="size-20 text-emerald-600 mx-auto mb-4" strokeWidth={1.5} />
                <h2 className="text-2xl font-semibold text-emerald-600 mb-2">
                  太棒了！全部通过
                </h2>
                <p className="text-muted-foreground mb-2">
                  {firstTimeCorrect && starsEarned > 0 ? (
                    <span className="text-amber-600 font-medium flex items-center justify-center gap-1">
                      <Star className="size-5 fill-amber-500" strokeWidth={1.5} />
                      +{starsEarned}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">已获得星星</span>
                  )}
                </p>
                {promoted && (
                  <p className="text-amber-600 font-bold mb-4 flex items-center justify-center gap-1">
                    <PartyPopper className="size-5" strokeWidth={1.5} />
                    恭喜晋级！
                  </p>
                )}
                {!promoted && (
                  <p className="text-muted-foreground mb-4">
                    继续挑战下一题
                  </p>
                )}
              </>
            ) : (
              <>
                <XCircle className="size-20 text-red-600 mx-auto mb-4" strokeWidth={1.5} />
                <h2 className="text-2xl font-semibold text-red-600 mb-2">
                  答案错误
                </h2>
                <p className="text-muted-foreground mb-6">
                  通过 {passedCount}/{totalCount} 个测试点
                  {firstTimeWrong && starsEarned < 0 && (
                    <span className="text-red-600 ml-2 flex items-center">
                      <Star className="size-4 text-red-600" strokeWidth={1.5} />
                      {starsEarned}
                    </span>
                  )}
                </p>
                {demoted && (
                  <p className="text-red-600 font-bold mb-4 flex items-center justify-center gap-1">
                    <Frown className="size-5" strokeWidth={1.5} />
                    段位下降...
                  </p>
                )}
              </>
            )}

            <div className="flex gap-3 justify-center">
              <Button
                type="button"
                variant="outline"
                size="lg"
                onClick={onStay}
              >
                留在本题
              </Button>
              {canGoNext && (
                <Button
                  type="button"
                  size="lg"
                  onClick={onNext}
                >
                  下一题
                  <ArrowRight className="size-4 ml-2" strokeWidth={1.5} />
                </Button>
              )}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

// ========================================
// Exercise Navigation Component
// ========================================

interface ExerciseNavigationProps {
  exercises: ExerciseProgress[];
  currentIndex: number;
  onSwitch: (index: number) => void;
}

export function ExerciseNavigation({
  exercises,
  currentIndex,
  onSwitch,
}: ExerciseNavigationProps) {
  let start = currentIndex - NAV_CENTER_INDEX;
  let end = start + NAV_MAX_VISIBLE;

  if (start < 0) {
    start = 0;
    end = Math.min(exercises.length, NAV_MAX_VISIBLE);
  }

  if (end > exercises.length) {
    end = exercises.length;
    start = Math.max(0, end - NAV_MAX_VISIBLE);
  }

  const visibleExercises = exercises.slice(start, end);

  return (
    <div className="flex items-center gap-1.5">
      {visibleExercises.map((ex, idx) => {
        const globalIndex = start + idx;
        const isCurrent = globalIndex === currentIndex;

        return (
          <Button
            type="button"
            key={ex.exercise_id}
            onClick={() => ex.is_unlocked && onSwitch(globalIndex)}
            disabled={!ex.is_unlocked}
            title={`第 ${globalIndex + 1} 题: ${ex.title || "未命名"}`}
            className={`rounded-lg text-xs font-bold transition-colors duration-300 ease-out ${
              isCurrent
                ? "size-10 bg-primary text-primary-foreground z-10 hover:bg-primary/90"
                : ex.is_correct
                  ? "size-8 bg-emerald-50 text-emerald-700 border-2 border-emerald-500 hover:bg-emerald-50"
                  : ex.is_completed
                    ? "size-8 bg-red-50 text-red-700 border-2 border-red-500 hover:bg-red-50"
                    : ex.is_unlocked
                      ? "size-8 bg-card text-muted-foreground border border-border hover:border-primary"
                      : "size-8 bg-muted text-muted-foreground border border-border cursor-not-allowed"
            }`}
          >
            {globalIndex + 1}
          </Button>
        );
      })}
    </div>
  );
}

// ========================================
// Exercise List Modal Component
// ========================================

interface ExerciseListModalProps {
  isOpen: boolean;
  onClose: () => void;
  exercises: ExerciseProgress[];
  currentIndex: number;
  onSwitch: (index: number) => void;
}

export function ExerciseListModal({
  isOpen,
  onClose,
  exercises,
  currentIndex,
  onSwitch,
}: ExerciseListModalProps) {
  if (!isOpen) return null;

  const handleSwitch = (index: number) => {
    if (exercises[index]?.is_unlocked) {
      onSwitch(index);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="absolute inset-0 h-full w-full rounded-none bg-black/50 hover:bg-black/50 p-0"
        aria-label="关闭"
        onClick={onClose}
      />
      <div
        className="relative max-w-lg w-full mx-4 max-h-[70vh] overflow-hidden rounded-lg flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <Panel className="h-full flex flex-col">
        <div className="flex justify-between items-center px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">题目列表</h3>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="关闭"
          >
            <X className="size-5" strokeWidth={1.5} />
          </Button>
        </div>

        <div className="overflow-y-auto flex-1 p-2 gap-y-2">
          {exercises.map((ex, index) => (
            <Button
              type="button"
              key={ex.exercise_id}
              variant="ghost"
              onClick={() => handleSwitch(index)}
              disabled={!ex.is_unlocked}
              className={`w-full h-auto justify-start text-left px-4 py-3 rounded-lg transition-colors flex items-center gap-3 ${
                index === currentIndex
                  ? "bg-primary/10 border border-primary"
                  : ex.is_unlocked
                    ? "hover:bg-secondary border border-transparent"
                    : "opacity-50 cursor-not-allowed border border-transparent"
              }`}
            >
              <span
                className={`size-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                  index === currentIndex
                    ? "bg-primary text-primary-foreground"
                    : ex.is_correct
                      ? "bg-emerald-50 text-emerald-700 border-2 border-emerald-500"
                      : ex.is_completed
                        ? "bg-red-50 text-red-700 border-2 border-red-500"
                        : ex.is_unlocked
                          ? "bg-muted text-muted-foreground"
                          : "bg-muted text-muted-foreground"
                }`}
              >
                {index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-foreground truncate">
                  {ex.title || `第 ${index + 1} 题`}
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <span>难度:</span>
                  <span className="flex items-center gap-0.5">
                    {Array.from({ length: ex.difficulty || 1 }).map((_, i) => (
                      <Star key={i} className="size-3 fill-amber-500 text-amber-500" strokeWidth={1.5} />
                    ))}
                  </span>
                  {ex.is_completed && (
                    <span
                      className={`ml-2 ${ex.is_correct ? "text-emerald-600" : "text-red-600"}`}
                    >
                      {ex.is_correct ? "已答对" : "已答错"}
                    </span>
                  )}
                </div>
              </div>
              {!ex.is_unlocked && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Lock className="size-3" strokeWidth={1.5} />
                  未解锁
                </span>
              )}
            </Button>
          ))}
        </div>

        <div className="px-6 py-4 border-t border-border text-center text-sm text-muted-foreground">
          已完成 {exercises.filter((e) => e.is_completed).length} 题
        </div>
      </Panel>
      </div>
    </div>
  );
}
