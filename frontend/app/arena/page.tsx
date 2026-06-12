"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, useRef, Suspense } from "react";
import {
  X,
  CheckCircle,
  XCircle,
  ArrowRight,
  RotateCcw,
  Zap,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Code2,
  Send,
  Star,
  AlertTriangle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import "katex/dist/katex.min.css";
import {
  startInfiniteSession,
  getChallengeProgress,
  submitChallengeExercise,
  saveChallengeCode,
  switchChallengeExercise,
  appendChallengeExercises,
  startStageSession,
  TIER_NAMES,
  TIER_COLORS,
  getStoredToken,
} from "@/lib/api";
import { getGlobalTierInfo } from "@/lib/api/tier";
import { getChallengeExerciseContent } from "@/lib/api/learning-path";
import { endLearningSessionKeepalive } from "@/lib/api/stats";
import { executeCode, executeCodeBatch } from "@/lib/api/code";
import { CodeEditorPanel } from "@/components/exercise/CodeEditorPanel";
import { SampleIOCard } from "@/components/exercise/SampleIOCard";
import {
  CustomTestInput,
  TestOutputDisplay,
} from "@/components/exercise/CustomTestInput";
import {
  LuoguTestCaseTable,
  LuoguTestCasesSummary,
} from "@/components/exercise/LuoguTestCaseTable";
import { FavoriteButton } from "@/components/exercise/FavoriteButton";
import { StreamHintPanel, type ExerciseHintData } from "@/components/exercise/AIHintPanel";
import { getTemplate } from "@/lib/codeTemplates";
import {
  getCoreBalance,
} from "@/lib/api/core";
import type {
  ChallengeExercise,
} from "@/types/api";
import {
  Exercise,
  TestCaseResult,
  ExerciseProgress,
  ProgressExercise,
  ChallengeProgressResponse,
  TestCase,
  FeedbackState,
  RightPanelTab,
  LANGUAGE_MAP,
  LANGUAGE_OPTIONS,
  DIFFICULTY_NAMES,
} from "./types"
import { ResultModal, ExerciseNavigation, ExerciseListModal, TierProgressBar } from "./components"
import { useArenaSession } from "./use-arena-session"
import { useCodeRunner } from "./use-code-runner"

export const metadata = {
  title: '竞技场 - 智码领航',
  description: '挑战之路编程竞技场',
}

function ArenaContent() {
  const session = useArenaSession()
  const runner = useCodeRunner()

  const {
    push,
    exercises,
    exerciseProgress,
    currentIndex,
    loading,
    tierInfo,
    coreBalance,
    contentLoadingMap,
    contentErrorMap,
    savedCodesRef,
    sessionIdRef,
    currentDifficultyRef,
    switchToExercise,
    handleNext,
    handleStay,
    handleRetry,
    handleExitSave,
    handleExit,
    endTrackedSession,
    setExerciseProgress,
    setExercises,
    loadExerciseContent,
    showExerciseList,
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
    setCustomTestInput,
    customTestOutput,
    setCustomTestOutput,
    isCustomRunning,
    setIsCustomRunning,
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
  const currentProgress = exerciseProgress[currentIndex]

  const getLanguageId = () => LANGUAGE_MAP[language]?.id || 71;
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

  // ========================================
  // Test execution
  // ========================================

  const handleSubmit = async () => {
    if (!exercises[currentIndex] || isSubmitting) return;

    const currentExercise = exercises[currentIndex];

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
      } else if (submitResult.new_stars !== undefined && tierInfo) {
        // Always update stars count (includes case when re-submitting)
        setTierInfo(prev => prev ? ({
          ...prev,
          stars: submitResult.new_stars,
        }) : prev);
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
  };

  // ========================================
  // Navigation
  // ========================================

  const canGoNext = currentIndex < exercises.length - 1

  const problemContent = currentExercise ? (
    <div className="p-6">
      {contentLoadingMap[currentExercise.id] ? (
        <div className="mb-6 p-4 bg-secondary rounded-lg">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" strokeWidth={1.5} />
            正在加载题面...
          </div>
        </div>
      ) : contentErrorMap[currentExercise.id] ? (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-red-600 mb-2">
            <AlertTriangle className="size-4" strokeWidth={1.5} />
            题面加载失败
          </div>
          <p className="text-xs text-red-600 mb-3">{contentErrorMap[currentExercise.id]}</p>
          <button
            type="button"
            onClick={() => loadExerciseContent(currentExercise.id, currentIndex, language)}
            className="px-3 py-1.5 bg-card border border-red-500 text-red-600 text-xs rounded-md hover:bg-red-50 transition-colors"
          >
            重试
          </button>
        </div>
      ) : currentExercise.content.description ? (
        <div className="text-muted-foreground leading-relaxed mb-6">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={{
              h1: ({ children }) => <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>,
              h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mt-4 mb-2 border-b border-border pb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-base font-semibold text-foreground mt-3 mb-2">{children}</h3>,
              p: ({ children }) => <p className="text-muted-foreground mb-2 leading-relaxed">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>,
              li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
              blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/20 pl-4 italic my-2 text-muted-foreground">{children}</blockquote>,
              strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code className="bg-secondary px-1.5 py-0.5 rounded text-sm text-red-600 font-mono border border-border" {...props}>
                    {children}
                  </code>
                ) : (
                  <code className={className} {...props}>{children}</code>
                );
              },
              pre: ({ children }) => (
                <pre
                  className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3 bg-slate-900 text-slate-100 border border-slate-700"
                >
                  {children}
                </pre>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-3">
                  <table className="min-w-full border-collapse border border-border">{children}</table>
                </div>
              ),
              thead: ({ children }) => <thead className="bg-secondary">{children}</thead>,
              th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground border border-border">{children}</th>,
              td: ({ children }) => <td className="px-3 py-2 text-sm text-muted-foreground border border-border">{children}</td>,
            }}
          >
            {currentExercise.content.description}
          </ReactMarkdown>
        </div>
      ) : null}

      {/* Sample I/O */}
      {currentExercise.content.samples &&
      currentExercise.content.samples.length > 0 ? (
        <div className="mb-6">
          <SampleIOCard
            input={currentExercise.content.samples[0].input}
            output={currentExercise.content.samples[0].output}
            onRun={(input) =>
              handleSampleRun(
                input,
                currentExercise.content.samples![0].output,
              )
            }
            isRunning={isCustomRunning}
          />
        </div>
      ) : currentExercise.content.sample_input ||
        currentExercise.content.sample_output ? (
        <div className="mb-6">
          <SampleIOCard
            input={currentExercise.content.sample_input || ""}
            output={currentExercise.content.sample_output || ""}
            onRun={(input) =>
              handleSampleRun(
                input,
                currentExercise.content.sample_output,
              )
            }
            isRunning={isCustomRunning}
          />
        </div>
      ) : null}

      {currentExercise.knowledge_points.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {currentExercise.knowledge_points.map((kp) => (
            <span
              key={`arena-${currentExercise.id}-${kp}`}
              className="knowledge-tag px-3 py-1.5 text-primary text-xs rounded-lg font-medium"
            >
              {kp}
            </span>
          ))}
        </div>
      )}

      {/* AI Hint Panel */}
      <div className="mt-6">
        <StreamHintPanel
          exerciseData={{
            exercise_id: String(currentExercise.id),
            exercise_title: currentExercise.content.title || `题目 #${currentExercise.id}`,
            exercise_description: currentExercise.content.description || currentExercise.content.text || "",
            difficulty: currentExercise.difficulty,
            knowledge_points: currentExercise.knowledge_points || [],
            code_template: currentExercise.content.code_template,
            sample_input: currentExercise.content.sample_input,
            sample_output: currentExercise.content.sample_output,
          }}
          token={getStoredToken() || ""}
          onBalanceChange={async () => {
            const token = getStoredToken();
            if (token) {
              try {
                const { getCoreBalance } = await import("@/lib/api/core");
                const balanceData = await getCoreBalance();
                setCoreBalance(balanceData.balance);
              } catch {
                // 忽略刷新失败
              }
            }
          }}
          currentBalance={coreBalance}
          disabled={isSubmitting}
        />
      </div>
    </div>
  ) : null

  const codeEditor = (
    <CodeEditorPanel
      value={code}
      onChange={setCode}
      language={LANGUAGE_MAP[language]?.monaco || "python"}
    />
  )

  const outputContent = rightPanelTab === "output" && testResults.length > 0 ? (
    <div className="p-4 bg-background">
      <LuoguTestCaseTable
        results={testResults}
        passedCount={testResults.filter(r => r.passed).length}
        totalCount={testResults.length}
        isRunning={isSubmitting}
      />
    </div>
  ) : (
    <div>
      <CustomTestInput
        onRun={(input) => handleCustomRun(input, false)}
        isRunning={isCustomRunning}
        defaultInput={customTestInput}
      />
      {customTestOutput && (
        <div className="px-4 pb-4">
          <TestOutputDisplay
            output={customTestOutput.output}
            expected={customTestOutput.expected}
            passed={customTestOutput.passed}
            isRunning={isCustomRunning}
            error={customTestOutput.error}
          />
        </div>
      )}
    </div>
  )

  return (
    <div className="h-screen ide-container flex flex-col">
      {/* Top Bar */}
      <header className="flex-shrink-0 z-50 bg-card border-b border-border">
        <TierProgressBar
          tier={tierInfo?.tier || ""}
          subTier={tierInfo?.sub_tier || 1}
          stars={tierInfo?.stars || 0}
          fullName={tierInfo?.full_name || "加载中..."}
        />
        <div className="px-4 py-2 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button type="button" onClick={() => handleExit(code, language)} className="shrink-0 ide-header-back">
              <X className="size-4" strokeWidth={1.5} />
              <span className="text-sm hidden sm:inline">退出挑战</span>
            </button>
            {currentExercise && (
              <div className="flex items-center gap-3 min-w-0">
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold text-white difficulty-badge difficulty-${currentExercise.difficulty} shrink-0`}
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
              onSwitch={(idx: number) => switchToExercise(idx, language, (newCode: string) => { setCode(newCode); reset(); setRightPanelTab("code"); })}
            />
            <button type="button"
              onClick={() => setShowExerciseList(true)}
              className="px-3 py-1.5 bg-card border border-border rounded-lg text-xs text-muted-foreground hover:border-primary hover:text-primary transition-colors flex items-center gap-1.5"
            >
              <span>题目列表</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 min-h-0 overflow-hidden">
        {/* Desktop: 3-column grid */}
        <div className="h-full hidden lg:grid grid-cols-12 gap-0">
          {/* Problem */}
          <div className="col-span-4 ide-problem-panel">
            {problemContent}
          </div>

          {/* Code Editor */}
          <div className="col-span-5 ide-editor-panel flex flex-col">
            <div className="flex-shrink-0 flex items-center justify-between px-3 py-2 border-b border-border bg-card">
              <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                <Code2 className="size-4" strokeWidth={1.5} />
                代码
              </span>
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="px-2 py-1 text-xs font-medium text-muted-foreground bg-card border border-border rounded-md focus:outline-none focus:border-primary cursor-pointer"
              >
                {LANGUAGE_OPTIONS.map((lang) => (
                  <option key={lang.key} value={lang.key}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-h-0">
              {codeEditor}
            </div>
          </div>

          {/* Output / Tests */}
          <div className="col-span-3 bg-card border-l border-border flex flex-col">
            <div className="panel-tabs flex-shrink-0 flex items-center">
              <button type="button"
                onClick={() => setRightPanelTab("code")}
                className={`panel-tab ${rightPanelTab !== "output" ? "active" : ""}`}
              >
                <Code2 className="size-4 inline mr-1.5" strokeWidth={1.5} />
                测试
              </button>
              {testResults.length > 0 && (
                <button type="button"
                  onClick={() => setRightPanelTab("output")}
                  className={`panel-tab ${rightPanelTab === "output" ? "active" : ""}`}
                >
                  <CheckCircle className="size-4 inline mr-1.5" strokeWidth={1.5} />
                  结果
                </button>
              )}
            </div>
            <div className="flex-1 min-h-0 overflow-y-auto">
              {outputContent}
            </div>
          </div>
        </div>

        {/* Mobile/Tablet: tabs */}
        <div className="h-full flex flex-col lg:hidden">
          <div className="flex border-b border-border bg-card">
            <button type="button"
              onClick={() => setMobileTab("problem")}
              className={`flex-1 px-4 py-3 text-xs font-medium transition-colors ${mobileTab === "problem" ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              题目
            </button>
            <button type="button"
              onClick={() => setMobileTab("code")}
              className={`flex-1 px-4 py-3 text-xs font-medium transition-colors ${mobileTab === "code" ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              代码
            </button>
            <button type="button"
              onClick={() => setMobileTab("output")}
              className={`flex-1 px-4 py-3 text-xs font-medium transition-colors ${mobileTab === "output" ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              输出
            </button>
          </div>
          <div className="flex-1 min-h-0 overflow-hidden">
            {mobileTab === "problem" && (
              <div className="h-full ide-problem-panel overflow-y-auto">
                {problemContent}
              </div>
            )}
            {mobileTab === "code" && (
              <div className="h-full flex flex-col ide-editor-panel">
                <div className="flex-shrink-0 flex items-center justify-between px-3 py-2 border-b border-border bg-card">
                  <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                    <Code2 className="size-4" strokeWidth={1.5} />
                    代码
                  </span>
                  <select
                    value={language}
                    onChange={(e) => handleLanguageChange(e.target.value)}
                    className="px-2 py-1 text-xs font-medium text-muted-foreground bg-card border border-border rounded-md focus:outline-none focus:border-primary cursor-pointer"
                  >
                    {LANGUAGE_OPTIONS.map((lang) => (
                      <option key={lang.key} value={lang.key}>
                        {lang.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex-1 min-h-0">
                  {codeEditor}
                </div>
              </div>
            )}
            {mobileTab === "output" && (
              <div className="h-full bg-card overflow-y-auto">
                {outputContent}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Bottom Action Bar */}
      <div
        className={`ide-action-bar ${
          feedbackState === "correct"
            ? "ide-action-bar-success"
            : feedbackState === "wrong"
              ? "ide-action-bar-error"
              : "ide-action-bar-idle"
        }`}
      >
        <div className="px-6 py-4">
          {feedbackState === "idle" ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3">
                  <div className="size-10 bg-primary-50 rounded-lg flex items-center justify-center border border-primary/20">
                    <Zap className="size-5 text-amber-600" strokeWidth={1.5} />
                  </div>
                  <div>
                    <p className="text-sm text-foreground font-medium">
                      挑战之路
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {tierInfo ? (
                        <>
                          当前段位{" "}
                          <span className="font-medium" style={{ color: TIER_COLORS[tierInfo.tier as keyof typeof TIER_COLORS] || '#CD7F32' }}>
                            {tierInfo.full_name}
                          </span>
                          {" "}<span className="text-amber-600 flex items-center inline-flex"><Star className="size-3.5 fill-amber-500" strokeWidth={1.5} />{tierInfo.stars}</span>
                        </>
                      ) : (
                        "加载中..."
                      )}
                    </p>
                  </div>
                </div>

                {testResults.length > 0 && (
                  <>
                    <div className="h-6 w-px bg-border" />
                    <LuoguTestCasesSummary
                      passedCount={testResults.filter(r => r.passed).length}
                      totalCount={testResults.length}
                    />
                  </>
                )}
              </div>

              <div className="action-buttons-group">
                <button type="button"
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="btn-action btn-submit"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="size-4 animate-spin" strokeWidth={1.5} />
                      提交中...
                    </>
                  ) : (
                    <>
                      <Send className="size-4" strokeWidth={1.5} />
                      提交
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : feedbackState === "correct" ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-emerald-50 rounded-lg flex items-center justify-center border border-emerald-500 success-pulse">
                  <CheckCircle className="size-6 text-emerald-600" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="font-semibold text-emerald-600">
                    太棒了！全部通过
                  </p>
                  <p className="text-sm text-emerald-600/70">继续挑战下一题</p>
                </div>
              </div>
              <div className="action-buttons-group">
                <button type="button" onClick={handleRetry} className="btn-action btn-reset">
                  <RotateCcw className="size-4" strokeWidth={1.5} />
                  重新作答
                </button>
                {canGoNext && (
                  <button type="button"
                    onClick={handleNext}
                    className="btn-action btn-success"
                  >
                    下一题
                    <ArrowRight className="size-5" strokeWidth={1.5} />
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-red-50 rounded-lg flex items-center justify-center border border-red-500 error-shake">
                  <XCircle className="size-6 text-red-600" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="font-semibold text-red-600">答案错误</p>
                  {testResults.length > 0 && (
                    <p className="text-sm text-red-600/70">
                      通过 {testResults.filter(r => r.passed).length}/{testResults.length} 个测试点 ·
                      修改后重新提交
                    </p>
                  )}
                </div>
              </div>
              <div className="action-buttons-group">
                <button type="button" onClick={handleRetry} className="btn-action btn-reset">
                  <RotateCcw className="size-4" strokeWidth={1.5} />
                  重新作答
                </button>
                {testResults.length > 0 && (
                  <button type="button"
                    onClick={() => setRightPanelTab("output")}
                    className="btn-action btn-submit"
                  >
                    查看详情
                  </button>
                )}
                {canGoNext && (
                  <button type="button"
                    onClick={handleNext}
                    className="btn-action btn-success"
                  >
                    下一题
                    <ArrowRight className="size-5" strokeWidth={1.5} />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

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
        isOpen={showExerciseList}
        onClose={() => setShowExerciseList(false)}
        exercises={exerciseProgress}
        currentIndex={currentIndex}
        onSwitch={(idx: number) => switchToExercise(idx, language, (newCode: string) => { setCode(newCode); reset(); setRightPanelTab("code"); })}
      />
    </div>
  );
}

// 主组件 - 用 Suspense 包裹
export default function ArenaPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="size-8 animate-spin text-primary" strokeWidth={1.5} />
      </div>
    }>
      <ArenaContent />
    </Suspense>
  );
}
