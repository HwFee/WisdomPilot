"use client";

import type { BaseQuestionResponse } from "@/types/api";
import type { NoteResponse } from "@/types/api";
import { NoteEditor } from "@/components/notes/NoteEditor";
import { KnowledgeOrb } from "@/components/ui/knowledge-orb";
import { PageContainer, Grid } from "@/components/layout";
import { QuizHeader } from "./quiz-header";
import { QuestionContext } from "./question-context";
import { AnswerArea } from "./answer-area";
import { QuizActionBar } from "./quiz-action-bar";

interface BaseQuizViewProps {
  baseQuestions: BaseQuestionResponse[];
  currentQuestionIndex: number;
  baseAnswers: Map<number, string>;
  submitted: boolean;
  isCorrect: boolean;
  completedQuestionsMap: Map<number, boolean>;
  baseQuestionLoading: boolean;
  selectedChapterTitle: string;
  courseId: number;
  selectedChapterId: number | null;
  selectedSectionId: number | null;
  noteRefreshKey: number;
  showNoteEditor: boolean;
  editingNote: NoteResponse | null;
  setBaseAnswers: React.Dispatch<React.SetStateAction<Map<number, string>>>;
  setCurrentQuestionIndex: React.Dispatch<React.SetStateAction<number>>;
  setSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
  setIsCorrect: React.Dispatch<React.SetStateAction<boolean>>;
  setShowNoteEditor: React.Dispatch<React.SetStateAction<boolean>>;
  setEditingNote: React.Dispatch<React.SetStateAction<NoteResponse | null>>;
  setNoteRefreshKey: React.Dispatch<React.SetStateAction<number>>;
  onSubmit: () => void;
  onNext: () => void;
  onBackToChapters: () => void;
}

export function BaseQuizView(props: BaseQuizViewProps) {
  const {
    baseQuestions,
    currentQuestionIndex,
    baseAnswers,
    submitted,
    isCorrect,
    completedQuestionsMap,
    baseQuestionLoading,
    selectedChapterTitle,
    courseId,
    selectedChapterId,
    selectedSectionId,
    noteRefreshKey,
    showNoteEditor,
    editingNote,
    setBaseAnswers,
    setCurrentQuestionIndex,
    setSubmitted,
    setIsCorrect,
    setShowNoteEditor,
    setEditingNote,
    setNoteRefreshKey,
    onSubmit,
    onNext,
    onBackToChapters,
  } = props;

  const currentQuestion = baseQuestions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === baseQuestions.length - 1;

  return (
    <div className="min-h-screen bg-background">
      <QuizHeader
        selectedChapterTitle={selectedChapterTitle}
        onBackToChapters={onBackToChapters}
        baseQuestions={baseQuestions}
        currentQuestionIndex={currentQuestionIndex}
        completedQuestionsMap={completedQuestionsMap}
        setCurrentQuestionIndex={setCurrentQuestionIndex}
        setSubmitted={setSubmitted}
        setIsCorrect={setIsCorrect}
      />

      <main className="pt-20 pb-28">
        <PageContainer>
          <Grid>
            <QuestionContext
              currentQuestion={currentQuestion}
              currentQuestionIndex={currentQuestionIndex}
              totalQuestions={baseQuestions.length}
              courseId={courseId}
              selectedChapterId={selectedChapterId}
              selectedSectionId={selectedSectionId}
              noteRefreshKey={noteRefreshKey}
              setEditingNote={setEditingNote}
              setShowNoteEditor={setShowNoteEditor}
              submitted={submitted}
              isCorrect={isCorrect}
            />
            <AnswerArea
              currentQuestion={currentQuestion}
              baseAnswers={baseAnswers}
              setBaseAnswers={setBaseAnswers}
              submitted={submitted}
              isCorrect={isCorrect}
            />
          </Grid>
        </PageContainer>
      </main>

      <QuizActionBar
        submitted={submitted}
        isCorrect={isCorrect}
        isLastQuestion={isLastQuestion}
        baseQuestionLoading={baseQuestionLoading}
        currentQuestion={currentQuestion}
        baseAnswers={baseAnswers}
        currentQuestionIndex={currentQuestionIndex}
        totalQuestions={baseQuestions.length}
        onSubmit={onSubmit}
        onNext={onNext}
      />

      <KnowledgeOrb
        disabledForQuestion={!submitted}
        courseId={courseId}
        chapterId={selectedChapterId ?? undefined}
        sectionId={selectedSectionId ?? undefined}
        exerciseId={currentQuestion.id}
        knowledgePoints={currentQuestion.knowledge_points}
      />

      {showNoteEditor && (
        <NoteEditor
          note={editingNote}
          exerciseId={currentQuestion.id}
          courseId={courseId}
          chapterId={selectedChapterId || undefined}
          sectionId={selectedSectionId || undefined}
          knowledgePoints={currentQuestion.knowledge_points}
          prefillContent={currentQuestion.text}
          prefillTitle={currentQuestion.text ? `题目笔记: ${currentQuestion.text.slice(0, 30)}...` : undefined}
          source="question"
          onSave={() => {
            setNoteRefreshKey((prev) => prev + 1);
          }}
          onClose={() => {
            setShowNoteEditor(false);
            setEditingNote(null);
          }}
        />
      )}
    </div>
  );
}
