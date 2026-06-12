"use client";

import { ArrowLeft, BookOpen, CheckCircle, XCircle, ChevronRight, PartyPopper, Loader2 } from "lucide-react";
import type { BaseQuestionResponse } from "@/types/api";
import type { NoteResponse } from "@/types/api";
import { FavoriteButton } from "@/components/exercise/FavoriteButton";
import { NoteButton } from "@/components/exercise/NoteButton";
import { NoteEditor } from "@/components/notes/NoteEditor";
import { KnowledgeOrb } from "@/components/ui/knowledge-orb";
import { PageContainer, Grid } from "@/components/layout";
import { DIFFICULTY_COLORS, getQuestionType } from "../types";

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
    baseQuestions, currentQuestionIndex, baseAnswers, submitted, isCorrect,
    completedQuestionsMap, baseQuestionLoading, selectedChapterTitle, courseId,
    selectedChapterId, selectedSectionId, noteRefreshKey, showNoteEditor, editingNote,
    setBaseAnswers, setCurrentQuestionIndex, setSubmitted, setIsCorrect,
    setShowNoteEditor, setEditingNote, setNoteRefreshKey,
    onSubmit, onNext, onBackToChapters,
  } = props;

  const currentQuestion = baseQuestions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === baseQuestions.length - 1;

  return (
    <div className="min-h-screen bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
        <PageContainer className="h-14 flex items-center justify-between">
          <button type="button"
            onClick={onBackToChapters}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="size-4" strokeWidth={1.5} />
            <span className="text-sm">退出</span>
          </button>
          <div className="flex items-center gap-2">
            <BookOpen className="size-5 text-amber-600" strokeWidth={1.5} />
            <span className="font-semibold">{selectedChapterTitle}</span>
          </div>
          <div className="flex items-center gap-1.5">
            {(() => {
              const MAX_VISIBLE = 5;
              const CENTER_INDEX = 2;

              let start = currentQuestionIndex - CENTER_INDEX;
              let end = start + MAX_VISIBLE;

              if (start < 0) {
                start = 0;
                end = Math.min(baseQuestions.length, MAX_VISIBLE);
              }

              if (end > baseQuestions.length) {
                end = baseQuestions.length;
                start = Math.max(0, end - MAX_VISIBLE);
              }

              return baseQuestions.slice(start, end).map((q, idx) => {
                const globalIndex = start + idx;
                const isCompleted = completedQuestionsMap.has(q.id);
                const wasCorrect = completedQuestionsMap.get(q.id) || false;
                const isCurrent = globalIndex === currentQuestionIndex;

                return (
                  <button type="button"
                    key={q.id}
                    onClick={() => {
                      if (completedQuestionsMap.has(q.id) || globalIndex <= currentQuestionIndex) {
                        setCurrentQuestionIndex(globalIndex);
                        if (completedQuestionsMap.has(q.id)) {
                          setSubmitted(true);
                          setIsCorrect(completedQuestionsMap.get(q.id) || false);
                        } else {
                          setSubmitted(false);
                          setIsCorrect(false);
                        }
                      }
                    }}
                    title={`第 ${globalIndex + 1} 题`}
                    className={`rounded-lg text-xs font-bold transition-all ${
                      isCurrent
                        ? "size-10 bg-primary text-primary-foreground"
                        : isCompleted
                          ? wasCorrect
                            ? "size-8 bg-muted text-emerald-600 border-2 border-emerald-600"
                            : "size-8 bg-muted text-red-600 border-2 border-red-600"
                          : globalIndex <= currentQuestionIndex
                            ? "size-8 bg-muted text-muted-foreground border border-border hover:border-primary"
                            : "size-8 bg-muted text-muted-foreground/50 border border-border cursor-not-allowed"
                    }`}
                  >
                    {globalIndex + 1}
                  </button>
                );
              });
            })()}
          </div>
        </PageContainer>
      </header>

      <main className="pt-20 pb-28">
        <PageContainer>
          <Grid>
            {/* Question context */}
            <div className="col-span-12 lg:col-span-5 space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-muted text-amber-600 rounded-lg text-sm font-medium">
                    {currentQuestionIndex + 1} / {baseQuestions.length}
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
                    {currentQuestion.knowledge_points.map((kp) => (
                      <span
                        key={kp}
                        className="px-2 py-1 bg-secondary text-primary text-xs rounded-full"
                      >
                        {kp}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Answer area */}
            <div className="col-span-12 lg:col-span-7 space-y-6">
              {/* Choice Options */}
              {getQuestionType(currentQuestion) === "choice" &&
                currentQuestion.options &&
                currentQuestion.options.length > 0 && (
                  <div className="flex flex-col gap-y-3">
                    {currentQuestion.options.map((opt, i) => {
                      const optLabel = String.fromCharCode(65 + i);
                      const isSelected =
                        baseAnswers.get(currentQuestion.id) === optLabel;
                      const isCorrectOption =
                        currentQuestion.correct_answer?.toUpperCase() ===
                        optLabel;

                      return (
                        <button type="button"
                          key={optLabel}
                          onClick={() =>
                            !submitted &&
                            setBaseAnswers((prev) =>
                              new Map(prev).set(currentQuestion.id, optLabel),
                            )
                          }
                          disabled={submitted}
                          className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                            submitted
                              ? isSelected
                                ? isCorrect
                                  ? "border-emerald-600 bg-muted"
                                  : "border-red-600 bg-muted"
                                : isCorrectOption
                                  ? "border-emerald-600 bg-muted"
                                  : "border-border opacity-50"
                              : isSelected
                                ? "border-primary bg-muted"
                                : "border-border hover:border-muted hover:bg-muted"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span
                              className={`size-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                                submitted
                                  ? isSelected && isCorrect
                                    ? "bg-emerald-600 text-primary-foreground"
                                    : isSelected && !isCorrect
                                      ? "bg-red-600 text-primary-foreground"
                                      : isCorrectOption
                                        ? "bg-emerald-600 text-primary-foreground"
                                        : "bg-muted text-muted-foreground"
                                  : isSelected
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted text-muted-foreground"
                              }`}
                            >
                              {submitted && isCorrectOption ? (
                                <CheckCircle className="size-4" strokeWidth={1.5} />
                              ) : (
                                optLabel
                              )}
                            </span>
                            <span className="text-foreground">{opt}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

              {/* Fill Blank Input */}
              {getQuestionType(currentQuestion) === "fill_blank" && (
                <div className="flex flex-col gap-y-4">
                  <div className="bg-card rounded-lg border border-border p-4">
                    <label htmlFor="fill-blank-answer" className="block text-sm font-medium text-foreground mb-2">
                      请输入答案：
                    </label>
                    <input
                      id="fill-blank-answer"
                      type="text"
                      value={baseAnswers.get(currentQuestion.id) || ""}
                      onChange={(e) =>
                        !submitted &&
                        setBaseAnswers((prev) =>
                          new Map(prev).set(currentQuestion.id, e.target.value),
                        )
                      }
                      disabled={submitted}
                      placeholder="在此输入您的答案..."
                      className={`w-full p-4 rounded-lg border-2 bg-background text-foreground transition-all ${
                        submitted
                          ? isCorrect
                            ? "border-emerald-600 bg-muted"
                            : "border-red-600 bg-muted"
                          : "border-border focus:border-primary focus:outline-none"
                      } disabled:opacity-70`}
                    />
                  </div>

                  {submitted && (
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm font-medium text-foreground mb-1 flex items-center gap-1">
                        {isCorrect ? (
                          <>
                            <CheckCircle className="size-4 text-emerald-600" strokeWidth={1.5} />
                            正确！
                          </>
                        ) : (
                          <>
                            <XCircle className="size-4 text-red-600" strokeWidth={1.5} />
                            错误
                          </>
                        )}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        正确答案：
                        <span className="font-medium text-emerald-600">
                          {currentQuestion.correct_answer}
                        </span>
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Explanation after submission */}
              {submitted && currentQuestion.explanation && (
                <div className="mt-6 p-4 rounded-lg bg-muted">
                  <p className="text-sm font-medium text-foreground mb-2">解析</p>
                  <p className="text-sm text-muted-foreground">
                    {currentQuestion.explanation}
                  </p>
                </div>
              )}
            </div>
          </Grid>
        </PageContainer>
      </main>

      {/* Bottom action bar */}
      <div
        className={`fixed bottom-0 left-0 right-0 border-t transition-colors ${
          submitted
            ? isCorrect
              ? "bg-muted border-emerald-600/30"
              : "bg-muted border-red-600/20"
            : "bg-card border-border"
        }`}
      >
        <PageContainer className="p-4">
          <div className="text-center text-sm text-muted-foreground mb-3">
            {isLastQuestion ? (
              <span className="text-amber-600 font-medium flex items-center justify-center gap-1">
                <PartyPopper className="size-4" strokeWidth={1.5} />
                完成本题即可获得经验奖励！
              </span>
            ) : (
              <span>进度: {currentQuestionIndex + 1}/{baseQuestions.length} · 完成所有题目可获得经验奖励</span>
            )}
          </div>
          {submitted ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isCorrect ? (
                  <>
                    <CheckCircle className="size-6 text-emerald-600" strokeWidth={1.5} />
                    <span className="font-medium text-emerald-600">
                      正确！
                    </span>
                  </>
                ) : (
                  <>
                    <XCircle className="size-6 text-red-600" strokeWidth={1.5} />
                    <span className="font-medium text-red-600">错误</span>
                  </>
                )}
              </div>
              <button type="button"
                onClick={onNext}
                disabled={baseQuestionLoading}
                className="px-8 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
              >
                {baseQuestionLoading ? (
                  <Loader2 className="size-4" strokeWidth={1.5} />
                ) : (
                  <>
                    {isLastQuestion ? "查看结果" : "下一题"}
                    <ChevronRight className="size-4" strokeWidth={1.5} />
                  </>
                )}
              </button>
            </div>
          ) : (
            <button type="button"
              onClick={onSubmit}
              disabled={!baseAnswers.get(currentQuestion.id)}
              className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              提交答案
            </button>
          )}
        </PageContainer>
      </div>

      {/* AI Knowledge Assistant Orb - only available after submitting answer */}
      <KnowledgeOrb
        disabledForQuestion={!submitted}
        courseId={courseId}
        chapterId={selectedChapterId ?? undefined}
        sectionId={selectedSectionId ?? undefined}
        exerciseId={currentQuestion.id}
        knowledgePoints={currentQuestion.knowledge_points}
      />

      {/* Note Editor Modal */}
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
          onSave={(savedNote) => {
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
