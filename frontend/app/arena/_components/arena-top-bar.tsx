"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

import { TierProgressBar, ExerciseNavigation } from "../components";
import { FavoriteButton } from "@/components/exercise/FavoriteButton";
import { DIFFICULTY_NAMES } from "../types";
import type { Exercise, ExerciseProgress } from "../types";

type TierInfo = {
  tier: string;
  sub_tier: number;
  stars: number;
  full_name: string;
} | null;

export interface ArenaTopBarProps {
  tierInfo: TierInfo | null;
  currentExercise: Exercise | undefined;
  currentIndex: number;
  exerciseProgress: ExerciseProgress[];
  onExit: () => void;
  onSwitchExercise: (idx: number) => void;
  onShowExerciseList: () => void;
}

export function ArenaTopBar({
  tierInfo,
  currentExercise,
  currentIndex,
  exerciseProgress,
  onExit,
  onSwitchExercise,
  onShowExerciseList,
}: ArenaTopBarProps) {
  return (
    <header className="flex-shrink-0 z-50 bg-card border-b border-border">
      <TierProgressBar
        tier={tierInfo?.tier || ""}
        subTier={tierInfo?.sub_tier || 1}
        stars={tierInfo?.stars || 0}
        fullName={tierInfo?.full_name || "加载中..."}
      />
      <div className="px-4 py-2 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onExit}
            className="shrink-0 gap-1.5"
          >
            <X className="size-4" strokeWidth={1.5} />
            <span className="text-sm hidden sm:inline">退出挑战</span>
          </Button>
          {currentExercise && (
            <div className="flex items-center gap-3 min-w-0">
              <span
                className={`px-2.5 py-1 rounded-lg text-xs font-bold text-white overflow-hidden difficulty-${currentExercise.difficulty} shrink-0`}
              >
                {DIFFICULTY_NAMES[currentExercise.difficulty] ||
                  `难度 ${currentExercise.difficulty}`}
              </span>
              <span className="text-sm font-medium text-foreground truncate">
                {currentExercise.z_id && (
                  <span className="text-muted-foreground mr-2 font-normal">{currentExercise.z_id}</span>
                )}
                {currentExercise.content.title || `题目 ${currentIndex + 1}`}
              </span>
              <FavoriteButton
                exerciseKey={`arena-global-${currentExercise.id}`}
                exerciseId={currentExercise.id}
                exerciseContent={{
                  title: currentExercise.content.title,
                  text: currentExercise.content.text,
                  description: currentExercise.content.description,
                }}
                exerciseType={currentExercise.type}
                exerciseDifficulty={currentExercise.difficulty}
                knowledgePoints={currentExercise.knowledge_points}
                size="sm"
                showLabel={false}
              />
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <ExerciseNavigation
            exercises={exerciseProgress}
            currentIndex={currentIndex}
            onSwitch={onSwitchExercise}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onShowExerciseList}
            className="text-xs"
          >
            题目列表
          </Button>
        </div>
      </div>
    </header>
  );
}
