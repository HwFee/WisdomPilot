"use client";

import { useCallback, useMemo, useState } from "react";

import {
  TIER_NAMES,
  getStoredToken,
} from "@/lib/api";
import { executeCodeBatch } from "@/lib/api/code";
import { getTemplate } from "@/lib/codeTemplates";
import {
  Exercise,
  TestCaseResult,
  ExerciseProgress,
  ProgressExercise,
  ChallengeProgressResponse,
  FeedbackState,
  RightPanelTab,
  LANGUAGE_MAP,
} from "../types"
import { ResultModal, ExerciseListModal } from "../components"
import { useArenaSession } from "../use-arena-session"
import { useCodeRunner } from "../use-code-runner"
import { ArenaProblemPanel } from "./arena-problem-panel"
import { ArenaCodePanel } from "./arena-code-panel"
import { ArenaOutputPanel } from "./arena-output-panel"
import { ArenaTopBar } from "./arena-top-bar"
import { ArenaMainContent } from "./arena-main-content"
import { ArenaBottomBar } from "./arena-bottom-bar"
import {
  appendChallengeExercises,
  getChallengeProgress,
  submitChallengeExercise,
  saveChallengeCode,
} from "@/lib/api"

type TierInfo = {
  tier: string;
  sub_tier: number;
  stars: number;
  full_name: string;
} | null;

type ModalResultShape = {
  isCorrect: boolean;
  passedCount: number;
  totalCount: number;
  starsEarned: number;
  promoted: boolean;
  demoted: boolean;
  firstTimeCorrect: boolean;
  firstTimeWrong: boolean;
};

// ========================================
// Module-level helpers
// ========================================

async function performSubmit(args: {
  currentExercise: Exercise | undefined;
  exercises: Exercise[];
  currentIndex: number;
  exerciseProgress: ExerciseProgress[];
  code: string;
  language: string;
  isSubmitting: boolean;
  setIsSubmitting: (v: boolean) => void;
  setTestResults: (v: TestCaseResult[]) => void;
  setRightPanelTab: (v: RightPanelTab) => void;
  setFeedbackState: (v: FeedbackState) => void;
  setModalResult: (v: ModalResultShape) => void;
  setShowResultModal: (v: boolean) => void;
  setTierInfo: (v: TierInfo) => void;
  setCoreBalance: (v: number | undefined) => void;
  setExercises: (v: (prev: Exercise[]) => Exercise[]) => void;
  setExerciseProgress: (v: (prev: ExerciseProgress[]) => ExerciseProgress[]) => void;
  savedCodesRef: React.MutableRefObject<Record<number, Record<string, string>>>;
  currentDifficultyRef: React.MutableRefObject<number>;
  push: (url: string) => void;
}) {
  const {
    currentExercise: exerciseAtIndex,
    exercises,
    currentIndex,
    exerciseProgress,
    code,
    language,
    isSubmitting,
    setIsSubmitting,
    setTestResults,
    setRightPanelTab,
    setFeedbackState,
    setModalResult,
    setShowResultModal,
    setTierInfo,
    setExercises,
    setExerciseProgress,
    savedCodesRef,
    currentDifficultyRef,
    push,
  } = args;

  if (!exerciseAtIndex || isSubmitting) return;

  const currentExercise = exerciseAtIndex;

  setIsSubmitting(true);
  setTestResults([]);
  setRightPanelTab("output");

  try {
    const token = getStoredToken();
    if (!token) {
      push("/login");
      return;
    }

    const testCases = currentExercise.test_cases || [];

    if (testCases.length === 0) {
      setTestResults([
        {
          passed: false,
          input: "",
          expected: "",
          actual: "",
          message: "该题目暂无测试用例",
        },
      ]);
      setFeedbackState("wrong");
      setIsSubmitting(false);
      return;
    }

    const testCasesForApi = testCases.map((tc) => ({
      input: tc.input || "",
      expected_output: tc.output || "",
    }));

    const getLanguageId = () => LANGUAGE_MAP[language]?.id || 71;

    const batchResult = await executeCodeBatch(
      {
        code: code,
        language_id: getLanguageId(),
        test_cases: testCasesForApi,
      },
      token,
    );

    const results: TestCaseResult[] = batchResult.results.map((r, i) => ({
      passed: r.passed,
      input: testCases[i]?.input || "",
      expected: r.expected,
      actual: r.actual,
      message: r.message,
    }));

    setTestResults(results);

    const allPassed = batchResult.passed_count === batchResult.total_count;
    setFeedbackState(allPassed ? "correct" : "wrong");

    // Submit to backend (无 session 概念，独立于课程)
    const submitResult = await submitChallengeExercise(
      {
        exercise_id: currentExercise.id,
        code: code,
        language: language,
        test_results: results,
      },
      token,
    );

    const finalIsCorrect = submitResult.is_correct;
    setFeedbackState(finalIsCorrect ? "correct" : "wrong");

    // Update tier info from submit result
    if (submitResult.tier_changed && submitResult.new_tier) {
      setTierInfo({
        tier: submitResult.new_tier,
        sub_tier: submitResult.new_sub_tier || 4,
        stars: submitResult.new_stars,
        full_name: `${TIER_NAMES[submitResult.new_tier] || submitResult.new_tier}${submitResult.new_sub_tier ? ['I', 'II', 'III', 'IV', 'V'][submitResult.new_sub_tier - 1] : ''}`,
      });
    }

    // Update progress
    setExerciseProgress((prev) => {
      const newProgress = [...prev];
      const idx = newProgress.findIndex(
        (p) => p.exercise_id === currentExercise.id,
      );
      if (idx >= 0) {
        newProgress[idx] = {
          ...newProgress[idx],
          is_completed: true,
          is_correct: finalIsCorrect,
          is_unlocked: true,
        };

        // Unlock next exercise based on exercise_index (not array index)
        // This ensures correct sequential unlocking even if array order differs
        const currentExerciseIndex = newProgress[idx].exercise_index;
        const nextIdx = newProgress.findIndex(
          (p) => p.exercise_index === currentExerciseIndex + 1,
        );
        if (nextIdx !== -1 && !newProgress[nextIdx].is_unlocked) {
          newProgress[nextIdx] = { ...newProgress[nextIdx], is_unlocked: true };
        }
      }
      return newProgress;
    });

    // Save code for this language
    savedCodesRef.current = {
      ...savedCodesRef.current,
      [currentExercise.id]: {
        ...savedCodesRef.current[currentExercise.id],
        [language]: code,
      },
    };

    // 错题收集已在后端 submitChallengeExercise 中处理，前端不再重复调用

    // Show modal for correct answers
    if (finalIsCorrect) {
      setModalResult({
        isCorrect: true,
        passedCount: batchResult.passed_count,
        totalCount: batchResult.total_count,
        starsEarned: submitResult.stars_earned,
        promoted: submitResult.promoted,
        demoted: submitResult.demoted,
        firstTimeCorrect: submitResult.first_time_correct,
        firstTimeWrong: submitResult.first_time_wrong,
      });
      setShowResultModal(true);
    }

    // Auto-append more exercises when approaching the end
    // Trigger when: current exercise is within last 3 exercises and is completed
    const currentExerciseIdx = exerciseProgress.findIndex(
      (p) => p.exercise_id === currentExercise.id,
    );
    const remainingUncompleted = exerciseProgress
      .slice(currentExerciseIdx + 1)
      .filter((p) => !p.is_completed).length;

    if (remainingUncompleted <= 2) {
      try {
        const appendResult = await appendChallengeExercises(
          { count: 5, difficulty_level: currentDifficultyRef.current },
          token,
        );
        if (appendResult.new_exercise_ids.length > 0) {
          // Refresh progress with lite mode (content loaded on demand)
          const newProgressData = await getChallengeProgress(token, true);

          // Append new exercises to the list (lite: no content yet)
          const existingIds = new Set(exercises.map((e) => e.id));
          const newExercises: Exercise[] = [];
          for (const ex of newProgressData.exercises as ProgressExercise[]) {
            if (!existingIds.has(ex.exercise_id)) {
              newExercises.push({
                id: ex.exercise_id,
                type: "programming" as const,
                difficulty: ex.difficulty || 1,
                content: {
                  title: ex.title || `题目 ${ex.exercise_index + 1}`,
                  description: "",
                  code_template: getTemplate("python"),
                  sample_input: "",
                  sample_output: "",
                  samples: [],
                },
                knowledge_points: [],
                test_cases: [],
              });
            }
          }

          setExercises((prev) => [...prev, ...newExercises]);
          setExerciseProgress((prev) => [
            ...prev,
            ...newProgressData.exercises.filter(
              (ex: ExerciseProgress) =>
                !prev.find((p) => p.exercise_id === ex.exercise_id),
            ),
          ]);

          // Initialize saved codes for new exercises
          const newSavedCodes: Record<number, Record<string, string>> = {};
          newProgressData.exercises.forEach((ex: ExerciseProgress) => {
            if (!savedCodesRef.current[ex.exercise_id]) {
              newSavedCodes[ex.exercise_id] = {
                python: ex.saved_code || getTemplate("python"),
              };
            }
          });
          savedCodesRef.current = { ...savedCodesRef.current, ...newSavedCodes };
        }
      } catch (error) {
        console.error("[挑战之路] 追加题目失败:", error);
      }
    }
  } catch (error) {
    console.error("Failed to submit:", error);
    setFeedbackState("wrong");
    setTestResults([
      {
        passed: false,
        input: "",
        expected: "",
        actual: "",
        message: "提交失败，请重试",
      },
    ]);
  } finally {
    setIsSubmitting(false);
  }
}

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

  const handleSubmit = useCallback(() => {
    return performSubmit({
      currentExercise,
      exercises,
      currentIndex,
      exerciseProgress,
      code,
      language,
      isSubmitting,
      setIsSubmitting,
      setTestResults,
      setRightPanelTab,
      setFeedbackState,
      setModalResult: (v) => setModalResult(v),
      setShowResultModal,
      setTierInfo,
      setCoreBalance,
      setExercises: (updater) => setExercises(updater),
      setExerciseProgress: (updater) => setExerciseProgress(updater),
      savedCodesRef,
      currentDifficultyRef,
      push,
    });
  }, [
    currentExercise,
    exercises,
    currentIndex,
    exerciseProgress,
    code,
    language,
    isSubmitting,
    setIsSubmitting,
    setTestResults,
    setRightPanelTab,
    setFeedbackState,
    setModalResult,
    setShowResultModal,
    setTierInfo,
    setCoreBalance,
    setExercises,
    setExerciseProgress,
    savedCodesRef,
    currentDifficultyRef,
    push,
  ]);

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
