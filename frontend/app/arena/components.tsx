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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div
        className={`bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 transform transition-all ${
          isCorrect ? "border-2 border-[#52C41A]" : "border-2 border-[#E74C3C]"
        }`}
      >
        <div className="text-center">
          {isCorrect ? (
            <>
              <CheckCircle className="size-20 text-[#52C41A] mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-[#52C41A] mb-2">
                太棒了！全部通过
              </h2>
              <p className="text-[#606266] mb-2">
                {firstTimeCorrect && starsEarned > 0 ? (
                  <span className="text-yellow-500 font-medium flex items-center justify-center gap-1">
                    <Star className="size-5 fill-yellow-500" />
                    +{starsEarned}
                  </span>
                ) : (
                  <span className="text-[#909399]">已获得星星</span>
                )}
              </p>
              {promoted && (
                <p className="text-[#E6A23C] font-bold mb-4 flex items-center justify-center gap-1">
                  <PartyPopper className="size-5" />
                  恭喜晋级！
                </p>
              )}
              {!promoted && (
                <p className="text-[#909399] mb-4">
                  继续挑战下一题
                </p>
              )}
            </>
          ) : (
            <>
              <XCircle className="size-20 text-[#E74C3C] mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-[#E74C3C] mb-2">
                答案错误
              </h2>
              <p className="text-[#606266] mb-6">
                通过 {passedCount}/{totalCount} 个测试点
                {firstTimeWrong && starsEarned < 0 && (
                  <span className="text-red-500 ml-2 flex items-center">
                    <Star className="size-4 text-red-400" />
                    {starsEarned}
                  </span>
                )}
              </p>
              {demoted && (
                <p className="text-[#E74C3C] font-bold mb-4 flex items-center justify-center gap-1">
                  <Frown className="size-5" />
                  段位下降...
                </p>
              )}
            </>
          )}

          <div className="flex gap-3 justify-center">
            <button type="button"
              onClick={onStay}
              className="px-6 py-3 bg-white border border-[#E4E7ED] rounded-xl font-medium text-[#303133] hover:bg-[#F5F7FA] transition-colors"
            >
              留在本题
            </button>
            {canGoNext && (
              <button type="button"
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-[#3498DB] to-[#2980B9] text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
              >
                下一题
                <ArrowRight className="size-4" />
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
  const MAX_VISIBLE = 5;
  const CENTER_INDEX = 2;

  let start = currentIndex - CENTER_INDEX;
  let end = start + MAX_VISIBLE;

  if (start < 0) {
    start = 0;
    end = Math.min(exercises.length, MAX_VISIBLE);
  }

  if (end > exercises.length) {
    end = exercises.length;
    start = Math.max(0, end - MAX_VISIBLE);
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
            className={`rounded-lg text-xs font-bold transition-all duration-300 ease-out ${
              isCurrent
                ? "size-10 bg-[#3498DB] text-white scale-110 shadow-lg z-10"
                : ex.is_correct
                  ? "size-8 bg-[#D4EDDA] text-[#155724] border-2 border-[#28A745]"
                  : ex.is_completed
                    ? "size-8 bg-[#F8D7DA] text-[#721C24] border-2 border-[#DC3545]"
                    : ex.is_unlocked
                      ? "size-8 bg-white text-[#606266] border border-[#E4E7ED] hover:border-[#3498DB]"
                      : "size-8 bg-[#F5F7FA] text-[#C0C4CC] border border-[#E4E7ED] cursor-not-allowed"
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
      role="button"
      tabIndex={0}
      aria-label="关闭"
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClose(); } }}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl p-6 max-w-lg w-full mx-4 max-h-[70vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-[#303133]">题目列表</h3>
          <button type="button"
            onClick={onClose}
            className="text-[#909399] hover:text-[#606266]"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 gap-y-2">
          {exercises.map((ex, index) => (
            <button type="button"
              key={ex.exercise_id}
              onClick={() => handleSwitch(index)}
              disabled={!ex.is_unlocked}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${
                index === currentIndex
                  ? "bg-[#3498DB]/10 border border-[#3498DB]"
                  : ex.is_unlocked
                    ? "hover:bg-[#F5F7FA] border border-transparent"
                    : "opacity-50 cursor-not-allowed border border-transparent"
              }`}
            >
              <span
                className={`size-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                  index === currentIndex
                    ? "bg-[#3498DB] text-white"
                    : ex.is_correct
                      ? "bg-[#D4EDDA] text-[#155724] border-2 border-[#28A745]"
                      : ex.is_completed
                        ? "bg-[#F8D7DA] text-[#721C24] border-2 border-[#DC3545]"
                        : ex.is_unlocked
                          ? "bg-[#E4E7ED] text-[#606266]"
                          : "bg-[#F5F7FA] text-[#C0C4CC]"
                }`}
              >
                {index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-[#303133] truncate">
                  {ex.title || `第 ${index + 1} 题`}
                </div>
                <div className="text-xs text-[#909399]">
                  难度: {"★".repeat(ex.difficulty || 1)}
                  {ex.is_completed && (
                    <span
                      className={`ml-2 ${ex.is_correct ? "text-[#52C41A]" : "text-[#E74C3C]"}`}
                    >
                      {ex.is_correct ? "已答对" : "已答错"}
                    </span>
                  )}
                </div>
              </div>
              {!ex.is_unlocked && (
                <span className="text-xs text-[#C0C4CC] flex items-center gap-1">
                  <Lock className="size-3" />
                  未解锁
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-[#E4E7ED] text-center text-sm text-[#909399]">
          已完成 {exercises.filter((e) => e.is_completed).length} 题
        </div>
      </div>
    </div>
  );
}
