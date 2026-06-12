"use client";

import type { BaseQuestionResponse, NoteResponse } from "@/types/api";
import { FavoriteButton } from "@/components/exercise/FavoriteButton";
import { NoteButton } from "@/components/exercise/NoteButton";
import { DIFFICULTY_COLORS, getQuestionType } from "../types";

interface QuestionContextProps {
  currentQuestion: BaseQuestionResponse;
  currentQuestionIndex: number;
  totalQuestions: number;
  courseId: number;
  selectedChapterId: number | null;
  selectedSectionId: number | null;
  noteRefreshKey: number;
  setEditingNote: React.Dispatch<React.SetStateAction<NoteResponse | null>>;
  setShowNoteEditor: React.Dispatch<React.SetStateAction<boolean>>;
  submitted: boolean;
  isCorrect: boolean;
}

export function QuestionContext({
  currentQuestion,
  currentQuestionIndex,
  totalQuestions,
  courseId,
  selectedChapterId,
  selectedSectionId,
  noteRefreshKey,
  setEditingNote,
  setShowNoteEditor,
  submitted,
  isCorrect,
}: QuestionContextProps) {
  return (
    <div className="col-span-12 lg:col-span-5 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-muted text-amber-600 rounded-lg text-sm font-medium">
            {currentQuestionIndex + 1} / {totalQuestions}
          </span>
          <span
            className={`px-3 py-1 rounded-lg text-xs font-medium border ${DIFFICULTY_COLORS[currentQuestion.difficulty]}`}
          >
            {currentQuestion.difficulty === 1 ? "入门" : "基础"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <FavoriteButton
            exerciseKey={`mastery-${courseId}-${selectedChapterId}-${currentQuestion.id}`}
            courseId={courseId}
            exerciseId={currentQuestion.id}
            chapterId={selectedChapterId || undefined}
            sectionId={selectedSectionId || undefined}
            exerciseContent={{
              text: currentQuestion.text,
              options: currentQuestion.options,
            }}
            exerciseType={getQuestionType(currentQuestion)}
            exerciseDifficulty={currentQuestion.difficulty}
            knowledgePoints={currentQuestion.knowledge_points}
            size="sm"
          />
          <NoteButton
            courseId={courseId}
            exerciseId={currentQuestion.id}
            chapterId={selectedChapterId || undefined}
            knowledgePoints={currentQuestion.knowledge_points}
            size="sm"
            refreshKey={noteRefreshKey}
            onClick={(existingNote) => {
              setEditingNote(existingNote);
              setShowNoteEditor(true);
            }}
          />
        </div>
      </div>

      <div className="mb-4">
        <span className="px-3 py-1 bg-muted text-primary rounded-lg text-xs font-medium">
          {getQuestionType(currentQuestion) === "choice" ? "选择题" : "填空题"}
        </span>
      </div>

      <div
        className="bg-card border border-border p-6"
        data-question-context
        data-question-type={getQuestionType(currentQuestion)}
        data-question-id={currentQuestion.id}
        data-question-text={currentQuestion.text}
        data-question-options={JSON.stringify(currentQuestion.options || [])}
        data-question-answer-status={submitted ? (isCorrect ? "correct" : "wrong") : "unanswered"}
      >
        <h2 className="text-xl font-semibold text-foreground mb-4">
          {currentQuestion.text}
        </h2>

        {currentQuestion.knowledge_points.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {currentQuestion.knowledge_points.map((point) => (
              <span
                key={point}
                className="px-2 py-1 bg-secondary text-primary text-xs rounded-full"
              >
                {point}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
