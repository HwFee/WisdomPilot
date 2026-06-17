"use client";

import { useMemo, useState } from "react";

import {
  getStoredToken,
  saveChallengeCode,
} from "@/lib/api";
import { getTemplate } from "@/lib/codeTemplates";
import {
  Exercise,
  LANGUAGE_MAP,
} from "../types"
import { ResultModal, ExerciseListModal } from "../components"
import { useArenaSession } from "../use-arena-session"
import { useCodeRunner } from "../use-code-runner"
import { useChallengeSubmit } from "../use-challenge-submit"
import { ArenaProblemPanel } from "./arena-problem-panel"
import { ArenaCodePanel } from "./arena-code-panel"
import { ArenaOutputPanel } from "./arena-output-panel"
import { ArenaTopBar } from "./arena-top-bar"
import { ArenaMainContent } from "./arena-main-content"
import { ArenaBottomBar } from "./arena-bottom-bar"

// ========================================
// Main component
// ========================================

export function ArenaContent() {
  const session = useArenaSession()
  const runner = useCodeRunner()

  const {
    push,
    exercises,
    exerciseProgress,
    currentIndex,
    tierInfo,
    coreBalance,
    contentLoadingMap,
    contentErrorMap,
    savedCodesRef,
    currentDifficultyRef,
    switchToExercise,
    handleNext,
    handleStay,
    handleRetry,
    handleExit,
    setExercises,
    setExerciseProgress,
    loadExerciseContent,
    setShowExerciseList,
    setTierInfo,
    setCoreBalance,
  } = session

  const {
    code,
    setCode,
    language,
    setLanguage,
    feedbackState,
    setFeedbackState,
    testResults,
    setTestResults,
    isSubmitting,
    setIsSubmitting,
    customTestInput,
    customTestOutput,
    isCustomRunning,
    rightPanelTab,
    setRightPanelTab,
    showResultModal,
    setShowResultModal,
    modalResult,
    setModalResult,
    codeRef,
    reset,
    handleCustomRun,
    handleSampleRun,
  } = runner

  const [mobileTab, setMobileTab] = useState<"problem" | "code" | "output">("problem")

  const currentExercise = exercises[currentIndex]

  const canGoNext = currentIndex < exercises.length - 1

  const handleLanguageChange = (newLang: string) => {
    if (newLang === language) return;

    const currentExercise = exercises[currentIndex];
    if (!currentExercise) return;

    // Save current code for current language
    savedCodesRef.current = {
      ...savedCodesRef.current,
      [currentExercise.id]: {
        ...savedCodesRef.current[currentExercise.id],
        [language]: codeRef.current,
      },
    };

    // Switch language
    setLanguage(newLang);
    localStorage.setItem("preferred_language", newLang);

    // Restore code for new language or use template
    const savedCodeForNewLang = savedCodesRef.current[currentExercise.id]?.[newLang];
    if (savedCodeForNewLang) {
      setCode(savedCodeForNewLang);
    } else {
      setCode(getTemplate(newLang));
    }

    // Save to backend (无 session 概念，独立于课程)
    const token = getStoredToken();
    if (token) {
      saveChallengeCode(
        {
          exercise_id: currentExercise.id,
          code: codeRef.current,
          language: language,
        },
        token,
      ).catch(console.error);
    }
  };

  const handleSubmit = useChallengeSubmit({
    currentExercise,
    exercises,
    exerciseProgress,
    code,
    language,
    isSubmitting,
    savedCodesRef,
    currentDifficultyRef,
    setIsSubmitting,
    setTestResults,
    setRightPanelTab,
    setFeedbackState,
    setModalResult,
    setShowResultModal,
    setTierInfo,
    setExercises,
    setExerciseProgress,
    push,
    LANGUAGE_MAP,
  })

  const problemPanel = useMemo(
    () => (
      <ArenaProblemPanel
        currentExercise={currentExercise}
        currentIndex={currentIndex}
        contentLoadingMap={contentLoadingMap}
        contentErrorMap={contentErrorMap}
        language={language}
        loadExerciseContent={loadExerciseContent}
        isCustomRunning={isCustomRunning}
        handleSampleRun={handleSampleRun}
        coreBalance={coreBalance}
        setCoreBalance={setCoreBalance}
        isSubmitting={isSubmitting}
      />
    ),
    [currentExercise, currentIndex, contentLoadingMap, contentErrorMap, language, loadExerciseContent, isCustomRunning, handleSampleRun, coreBalance, setCoreBalance, isSubmitting],
  )

  const codeEditor = useMemo(
    () => (
      <ArenaCodePanel
        code={code}
        setCode={setCode}
        language={language}
      />
    ),
    [code, setCode, language],
  )

  const outputContent = useMemo(
    () => (
      <ArenaOutputPanel
        rightPanelTab={rightPanelTab}
        testResults={testResults}
        isSubmitting={isSubmitting}
        handleCustomRun={handleCustomRun}
        isCustomRunning={isCustomRunning}
        customTestInput={customTestInput}
        customTestOutput={customTestOutput}
      />
    ),
    [rightPanelTab, testResults, isSubmitting, handleCustomRun, isCustomRunning, customTestInput, customTestOutput],
  )

  return (
    <div className="h-screen ide-container flex flex-col">
      <ArenaTopBar
        tierInfo={tierInfo}
        currentExercise={currentExercise}
        currentIndex={currentIndex}
        exerciseProgress={exerciseProgress}
        onExit={() => handleExit(code, language)}
        onSwitchExercise={(idx) => switchToExercise(idx, language, (newCode) => { setCode(newCode); reset(); setRightPanelTab("code"); })}
        onShowExerciseList={() => setShowExerciseList(true)}
      />

      <ArenaMainContent
        problemPanel={problemPanel}
        codeEditor={codeEditor}
        outputContent={outputContent}
        mobileTab={mobileTab}
        setMobileTab={setMobileTab}
        language={language}
        onLanguageChange={handleLanguageChange}
        rightPanelTab={rightPanelTab}
        setRightPanelTab={setRightPanelTab}
        testResults={testResults}
      />

      <ArenaBottomBar
        feedbackState={feedbackState}
        tierInfo={tierInfo}
        testResults={testResults}
        isSubmitting={isSubmitting}
        canGoNext={canGoNext}
        onSubmit={handleSubmit}
        onRetry={handleRetry}
        onNext={handleNext}
        onShowOutput={() => setRightPanelTab("output")}
      />

      {/* Result Modal */}
      {showResultModal && modalResult && (
        <ResultModal
          isCorrect={modalResult.isCorrect}
          passedCount={modalResult.passedCount}
          totalCount={modalResult.totalCount}
          starsEarned={modalResult.starsEarned}
          promoted={modalResult.promoted}
          demoted={modalResult.demoted}
          firstTimeCorrect={modalResult.firstTimeCorrect}
          firstTimeWrong={modalResult.firstTimeWrong}
          onStay={handleStay}
          onNext={handleNext}
          canGoNext={canGoNext}
        />
      )}

      {/* 题目列表模态框 */}
      <ExerciseListModal
        isOpen={session.showExerciseList}
        onClose={() => setShowExerciseList(false)}
        exercises={exerciseProgress}
        currentIndex={currentIndex}
        onSwitch={(idx) => switchToExercise(idx, language, (newCode) => { setCode(newCode); reset(); setRightPanelTab("code"); })}
      />
    </div>
  );
}
