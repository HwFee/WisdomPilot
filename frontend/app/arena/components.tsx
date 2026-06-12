import {
  X,
  CheckCircle,
  XCircle,
  ArrowRight,
  Star,
  PartyPopper,
  Frown,
  Lock,
} from "lucide-react";
import type { ExerciseProgress } from "./types";

// ========================================
// Constants
// ========================================

const NAV_MAX_VISIBLE = 5;
const NAV_CENTER_INDEX = 2;

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
      <div
        className={`bg-card rounded-lg p-8 max-w-md w-full mx-4 border-2 ${
          isCorrect ? "border-emerald-500" : "border-red-500"
        }`}
      >
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
            <button type="button"
              onClick={onStay}
              className="px-6 py-3 bg-card border border-border rounded-lg font-medium text-foreground hover:bg-secondary transition-colors"
            >
              留在本题
            </button>
            {canGoNext && (
              <button type="button"
                onClick={onNext}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary-600 transition-colors flex items-center gap-2"
              >
                下一题
                <ArrowRight className="size-4" strokeWidth={1.5} />
              </button>
            )}
          </div>
        </div>
      </div>
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
          <button type="button"
            key={ex.exercise_id}
            onClick={() => ex.is_unlocked && onSwitch(globalIndex)}
            disabled={!ex.is_unlocked}
            title={`第 ${globalIndex + 1} 题: ${ex.title || "未命名"}`}
            className={`rounded-lg text-xs font-bold transition-colors duration-300 ease-out ${
              isCurrent
                ? "size-10 bg-primary text-primary-foreground z-10"
                : ex.is_correct
                  ? "size-8 bg-emerald-50 text-emerald-700 border-2 border-emerald-500"
                  : ex.is_completed
                    ? "size-8 bg-red-50 text-red-700 border-2 border-red-500"
                    : ex.is_unlocked
                      ? "size-8 bg-card text-muted-foreground border border-border hover:border-primary"
                      : "size-8 bg-muted text-muted-foreground border border-border cursor-not-allowed"
            }`}
          >
            {globalIndex + 1}
          </button>
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
      role="button"
      tabIndex={0}
      aria-label="关闭"
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClose(); } }}
    >
      <div
        className="bg-card rounded-lg p-6 max-w-lg w-full mx-4 max-h-[70vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-foreground">题目列表</h3>
          <button type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="size-5" strokeWidth={1.5} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 gap-y-2">
          {exercises.map((ex, index) => (
            <button type="button"
              key={ex.exercise_id}
              onClick={() => handleSwitch(index)}
              disabled={!ex.is_unlocked}
              className={`w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center gap-3 ${
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
            </button>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-border text-center text-sm text-muted-foreground">
          已完成 {exercises.filter((e) => e.is_completed).length} 题
        </div>
      </div>
    </div>
  );
}
