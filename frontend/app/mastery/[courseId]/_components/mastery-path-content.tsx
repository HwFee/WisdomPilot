"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { LazyMotion, domAnimation, m } from "framer-motion";
import { Loader2 } from "lucide-react";
import {
  ExerciseSkeleton,
  GeneratingIndicator,
} from "@/components/exercise/ExerciseSkeleton";
import {
  staggerContainer,
  staggerItem,
  fadeIn,
  scaleIn,
} from "@/lib/animations";

import { useMasterySession } from "../use-mastery-session";
import { useBaseQuiz } from "../use-base-quiz";
import { useEnhancedQuiz } from "../use-enhanced-quiz";
import { ResultView } from "../components/result-view";
import { AnalysisView } from "../components/analysis-view";
import { EnhancedQuizView } from "../components/enhanced-quiz-view";
import { BaseQuizView } from "../components/base-quiz-view";
import { ChapterListView } from "../components/chapter-list-view";

import { useMasteryPathState } from "./mastery-state";
import { useMasteryActions, useRefreshOverview } from "./use-mastery-actions";

export function MasteryPathContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  // react-doctor-disable-next-line react-compiler-destructure-method, react-doctor/react-compiler-destructure-method
  const getSearchParam = (name: string) => searchParams.get(name);
  const courseId = Number(params.courseId);

  const { state, setters } = useMasteryPathState();

  const session = useMasterySession(getSearchParam);
  const baseQuiz = useBaseQuiz();

  const refreshOverview = useRefreshOverview(
    courseId,
    setters.setOverview,
    setters.setCourseDetail,
    setters.setLoading,
  );

  useEffect(() => {
    void refreshOverview();
  }, [refreshOverview]);

  const enhancedQuiz = useEnhancedQuiz(
    courseId,
    state.selectedChapterId,
    state.selectedSectionId,
    session.currentSectionIdRef,
    state.baseResult,
    state.currentQuestionIndex,
    setters.setStep,
    setters.setCurrentQuestionIndex,
    baseQuiz.setSubmitted,
    baseQuiz.setIsCorrect,
    baseQuiz.setCompletedQuestionsMap,
  );

  const actions = useMasteryActions({
    courseId,
    state,
    setters,
    searchParams,
    getSearchParam,
    session: {
      startTrackedSession: session.startTrackedSession,
      endTrackedSession: session.endTrackedSession,
      currentSectionIdRef: session.currentSectionIdRef,
    },
    baseQuiz: {
      baseAnswers: baseQuiz.baseAnswers,
      setBaseAnswers: baseQuiz.setBaseAnswers,
      submitted: baseQuiz.submitted,
      setSubmitted: baseQuiz.setSubmitted,
      isCorrect: baseQuiz.isCorrect,
      setIsCorrect: baseQuiz.setIsCorrect,
      completedQuestionsMap: baseQuiz.completedQuestionsMap,
      setCompletedQuestionsMap: baseQuiz.setCompletedQuestionsMap,
      checkAnswer: baseQuiz.checkAnswer,
      restoreSubmitState: baseQuiz.restoreSubmitState,
    },
    enhancedQuiz: {
      setEnhancedQuestions: enhancedQuiz.setEnhancedQuestions,
      setEnhancedAnswers: enhancedQuiz.setEnhancedAnswers,
      setFinalResult: enhancedQuiz.setFinalResult,
    },
    refreshOverview,
  });

  // Loading state - only show for select_chapter step
  if (state.loading && state.step === "select_chapter") {
    return (
      <LazyMotion features={domAnimation}>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <Loader2
              className="size-16 text-primary mx-auto mb-4"
              strokeWidth={1.5}
            />
            <p className="text-muted-foreground">加载中...</p>
          </m.div>
        </div>
      </LazyMotion>
    );
  }

  // Result state
  if (state.step === "result" && enhancedQuiz.finalResult) {
    return (
      <ResultView
        finalResult={enhancedQuiz.finalResult}
        onBackToChapters={actions.handleBackToChapters}
      />
    );
  }

  // Analysis state
  if (state.step === "analysis" && state.baseResult) {
    return (
      <AnalysisView
        baseResult={state.baseResult}
        enhancedLoading={enhancedQuiz.enhancedLoading}
        onViewQuestions={actions.handleViewQuestions}
        onBackToChapters={actions.handleBackToChapters}
        onStartEnhancedQuiz={enhancedQuiz.handleStartEnhancedQuiz}
      />
    );
  }

  // Enhanced quiz state
  if (state.step === "enhanced_quiz" && enhancedQuiz.enhancedQuestions.length > 0) {
    return (
      <EnhancedQuizView
        enhancedQuestions={enhancedQuiz.enhancedQuestions}
        currentQuestionIndex={state.currentQuestionIndex}
        enhancedAnswers={enhancedQuiz.enhancedAnswers}
        enhancedLoading={enhancedQuiz.enhancedLoading}
        generationStatus={enhancedQuiz.generationStatus}
        generationProgress={enhancedQuiz.generationProgress}
        submitted={baseQuiz.submitted}
        isCorrect={baseQuiz.isCorrect}
        setEnhancedAnswers={enhancedQuiz.setEnhancedAnswers}
        onSubmit={enhancedQuiz.handleSubmitEnhancedAnswer}
        onNext={enhancedQuiz.handleNextEnhancedQuestion}
        onBackToChapters={actions.handleBackToChapters}
      />
    );
  }

  // Base quiz state
  if (state.step === "base_quiz" && state.baseQuestions.length > 0) {
    return (
      <BaseQuizView
        baseQuestions={state.baseQuestions}
        currentQuestionIndex={state.currentQuestionIndex}
        baseAnswers={baseQuiz.baseAnswers}
        submitted={baseQuiz.submitted}
        isCorrect={baseQuiz.isCorrect}
        completedQuestionsMap={baseQuiz.completedQuestionsMap}
        baseQuestionLoading={state.baseQuestionLoading}
        selectedChapterTitle={state.selectedChapterTitle}
        courseId={courseId}
        selectedChapterId={state.selectedChapterId}
        selectedSectionId={state.selectedSectionId}
        noteRefreshKey={state.noteRefreshKey}
        showNoteEditor={state.showNoteEditor}
        editingNote={state.editingNote}
        setBaseAnswers={baseQuiz.setBaseAnswers}
        setCurrentQuestionIndex={setters.setCurrentQuestionIndex}
        setSubmitted={baseQuiz.setSubmitted}
        setIsCorrect={baseQuiz.setIsCorrect}
        setShowNoteEditor={setters.setShowNoteEditor}
        setEditingNote={setters.setEditingNote}
        setNoteRefreshKey={setters.setNoteRefreshKey}
        onSubmit={actions.handleSubmitBaseAnswer}
        onNext={actions.handleNextQuestion}
        onBackToChapters={actions.handleBackToChapters}
      />
    );
  }

  // Default: Chapter selection
  return (
    <ChapterListView
      overview={state.overview}
      courseDetail={state.courseDetail}
      onSelectChapter={actions.handleSelectChapter}
      courseId={courseId}
      selectedChapterId={state.selectedChapterId}
      selectedSectionId={state.selectedSectionId}
      baseQuestions={state.baseQuestions}
      currentQuestionIndex={state.currentQuestionIndex}
      showNoteEditor={state.showNoteEditor}
      editingNote={state.editingNote}
      setShowNoteEditor={setters.setShowNoteEditor}
      setEditingNote={setters.setEditingNote}
      setNoteRefreshKey={setters.setNoteRefreshKey}
      noteRefreshKey={state.noteRefreshKey}
    />
  );
}
