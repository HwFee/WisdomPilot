"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type {
  BaseAnswersSubmitResponse,
  EnhancedQuizQuestion,
  EnhancedQuizSubmitResponse,
} from "@/types/api";
import {
  getStoredToken,
  generateEnhancedQuiz,
  submitEnhancedQuiz,
} from "@/lib/api";
import {
  getGenerationStatus,
  persistEnhancedQuestion,
  saveMasteryExerciseProgress,
} from "@/lib/api/learning-path";
import { collectWrongQuestion } from "@/lib/api/wrong-question";
import type { MasteryStep } from "./types";

export function useEnhancedQuiz(
  courseId: number,
  selectedChapterId: number | null,
  selectedSectionId: number | null,
  currentSectionIdRef: React.RefObject<number | null>,
  baseResult: BaseAnswersSubmitResponse | null,
  currentQuestionIndex: number,
  setStep: (step: MasteryStep) => void,
  setCurrentQuestionIndex: React.Dispatch<React.SetStateAction<number>>,
  setSubmitted: React.Dispatch<React.SetStateAction<boolean>>,
  setIsCorrect: React.Dispatch<React.SetStateAction<boolean>>,
  setCompletedQuestionsMap: React.Dispatch<
    React.SetStateAction<Map<number, boolean>>
  >,
) {
  const [enhancedQuestions, setEnhancedQuestions] = useState<
    EnhancedQuizQuestion[]
  >([]);
  const enhancedSessionIdRef = useRef<string>("");
  const [enhancedLoading, setEnhancedLoading] = useState(false);
  const [enhancedAnswers, setEnhancedAnswers] = useState<Map<string, string>>(
    new Map(),
  );
  const [generationStatus, setGenerationStatus] = useState<
    "idle" | "generating" | "completed" | "failed"
  >("idle");
  const [generationProgress, setGenerationProgress] = useState({
    current: 0,
    total: 0,
  });
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null,
  );
  const [finalResult, setFinalResult] =
    useState<EnhancedQuizSubmitResponse | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  const startPollingForMoreExercises = useCallback(
    (sessionId: string, token: string) => {
      let lastExerciseCount = 1;

      pollingIntervalRef.current = setInterval(async () => {
        try {
          const status = await getGenerationStatus(sessionId, token);
          const newCount = status.exercises?.length || 0;

          if (newCount > lastExerciseCount) {
            lastExerciseCount = newCount;
            const newExercises = status.exercises.map((ex) => ({
              id: ex.id,
              type: ex.type as "choice" | "fill_blank",
              text: ex.text,
              options: ex.options || [],
              correct_answer: ex.correct_answer,
              explanation: ex.explanation,
              knowledge_points: ex.knowledge_points || [],
              difficulty: ex.difficulty,
            }));

            setEnhancedQuestions(newExercises);
            setGenerationProgress({
              current: status.generated_count,
              total: status.total_count,
            });
          }

          if (status.is_completed || status.status === "completed") {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            setGenerationStatus("completed");
          }

          if (status.status === "failed") {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            setGenerationStatus("failed");
            console.error("[精进之路] 题目生成失败");
          }
        } catch (e) {
          console.error("[精进之路] 轮询失败:", e);
        }
      }, 3000);
    },
    [],
  );

  const handleStartEnhancedQuiz = useCallback(async () => {
    const token = getStoredToken();
    if (!token || !selectedChapterId || !selectedSectionId) {
      console.error("[精进之路] handleStartEnhancedQuiz: 缺少必要参数", {
        selectedChapterId,
        selectedSectionId,
      });
      return;
    }

    currentSectionIdRef.current = selectedSectionId;
    setEnhancedLoading(true);
    setGenerationStatus("generating");

    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    try {
      const response = await generateEnhancedQuiz(
        courseId,
        {
          course_id: courseId,
          section_id: selectedSectionId,
          chapter_id: selectedChapterId,
          weak_points: baseResult?.weak_points || [],
          strong_points: baseResult?.strong_points || [],
          question_count: 3,
          question_types: ["choice", "fill_blank"],
        },
        token,
      );

      if (
        response.success &&
        response.questions &&
        response.questions.length > 0
      ) {
        setEnhancedQuestions(response.questions);
        enhancedSessionIdRef.current = response.session_id;
        setEnhancedAnswers(new Map());
        setCurrentQuestionIndex(0);
        setSubmitted(false);
        setStep("enhanced_quiz");
        setGenerationProgress({ current: 1, total: 3 });

        if (response.session_id) {
          startPollingForMoreExercises(response.session_id, token);
        }
      } else if (!response.success) {
        const failMsg = response.message || "生成强化测试失败";
        alert(failMsg);
        setGenerationStatus("failed");
      } else {
        setFinalResult({
          success: true,
          session_id: "",
          section_id: selectedSectionId,
          total_questions: baseResult?.total_questions || 0,
          correct_answers: baseResult?.correct_answers || 0,
          accuracy: baseResult?.accuracy || 0,
          xp_earned: 20,
          mastery_points_earned: 10,
          results: [],
          recommendations: ["表现优秀！所有知识点都已掌握。"],
          passed: true,
          message: "所有知识点已掌握！",
        });
        setStep("result");
        setGenerationStatus("completed");
      }
    } catch (error) {
      console.error("Failed to generate enhanced quiz:", error);
      const msg =
        error instanceof Error
          ? error.message
          : "生成强化测试失败，请稍后重试";
      alert(msg);
      setGenerationStatus("failed");
    } finally {
      setEnhancedLoading(false);
    }
  }, [
    courseId,
    selectedChapterId,
    selectedSectionId,
    baseResult,
    setStep,
    setCurrentQuestionIndex,
    setSubmitted,
    startPollingForMoreExercises,
    currentSectionIdRef,
  ]);

  const handleSubmitEnhancedAnswer = useCallback(
    async () => {
      const currentQuestion = enhancedQuestions[currentQuestionIndex];
      const answer = enhancedAnswers.get(currentQuestion.id);
      if (!answer) return;

      const correct =
        answer.toUpperCase() === currentQuestion.correct_answer?.toUpperCase();

      setIsCorrect(correct);
      setSubmitted(true);

      setCompletedQuestionsMap((prev) => {
        const newMap = new Map(prev);
        const questionId = parseInt(currentQuestion.id, 10);
        if (!isNaN(questionId)) {
          newMap.set(questionId, correct);
        }
        return newMap;
      });

      const token = getStoredToken();
      const sectionIdToSave =
        selectedSectionId ?? currentSectionIdRef.current ?? undefined;
      if (token && selectedChapterId && sectionIdToSave) {
        let questionId = parseInt(currentQuestion.id, 10);

        if (isNaN(questionId) && enhancedSessionIdRef.current) {
          const oldId = currentQuestion.id;
          try {
            const persistResult = await persistEnhancedQuestion(
              courseId,
              {
                session_id: enhancedSessionIdRef.current,
                question_index: currentQuestionIndex,
                section_id: sectionIdToSave,
                chapter_id: selectedChapterId,
              },
              token,
            );
            if (persistResult.success && persistResult.question_id) {
              questionId = persistResult.question_id;
              const newId = String(questionId);
              currentQuestion.id = newId;
              setEnhancedQuestions((prev) => {
                const next = [...prev];
                next[currentQuestionIndex] = {
                  ...next[currentQuestionIndex],
                  id: newId,
                };
                return next;
              });
              setEnhancedAnswers((prev) => {
                if (!prev.has(oldId)) return prev;
                const next = new Map(prev);
                const savedAnswer = next.get(oldId)!;
                next.delete(oldId);
                next.set(newId, savedAnswer);
                return next;
              });
            } else {
              console.error(
                "[精进之路-强化题] 持久化失败:",
                persistResult.message,
              );
            }
          } catch (error) {
            console.error(
              "[精进之路-强化题] 持久化接口调用失败:",
              error,
            );
          }
        }

        if (questionId && !isNaN(questionId)) {
          const exerciseKey = `mastery-${courseId}-${selectedChapterId}-${questionId}`;

          try {
            await saveMasteryExerciseProgress(
              {
                course_id: courseId,
                chapter_id: selectedChapterId,
                section_id: sectionIdToSave,
                question_id: questionId,
                question_index: currentQuestionIndex + 1,
                question_type: "enhanced",
                exercise_key: exerciseKey,
                is_completed: true,
                is_correct: correct,
                user_answer: answer,
                correct_answer: currentQuestion.correct_answer || "",
                attempt_count: 1,
              },
              token,
            );
          } catch (error) {
            console.error("[精进之路-强化题] 进度保存失败:", error);
          }

          if (!correct) {
            try {
              await collectWrongQuestion(token, {
                exercise_key: exerciseKey,
                user_answer: answer,
                course_id: courseId,
                chapter_id: selectedChapterId,
                section_id: selectedSectionId ?? undefined,
                exercise_id: questionId,
                exercise_content: {
                  text: currentQuestion.text,
                  options: currentQuestion.options,
                  type: "choice",
                },
                exercise_type: "choice",
                knowledge_points: currentQuestion.knowledge_points || [],
              });
            } catch (error) {
              console.error("[精进之路-强化题] 错题收集失败:", error);
            }
          }
        }
      }
    },
    [
      courseId,
      selectedChapterId,
      selectedSectionId,
      enhancedQuestions,
      enhancedAnswers,
      enhancedSessionIdRef,
      currentSectionIdRef,
      setIsCorrect,
      setSubmitted,
      setCompletedQuestionsMap,
      setEnhancedQuestions,
      setEnhancedAnswers,
    ],
  );

  const handleSubmitAllEnhancedAnswers = useCallback(async () => {
    const token = getStoredToken();
    if (!token || !selectedSectionId) return;

    setEnhancedLoading(true);

    try {
      const answersArray = Array.from(enhancedAnswers.entries()).map(
        ([questionId, answer]) => ({
          question_id: questionId,
          answer,
        }),
      );

      const result = await submitEnhancedQuiz(
        courseId,
        {
          session_id: enhancedSessionIdRef.current,
          section_id: selectedSectionId,
          answers: answersArray,
        },
        token,
      );

      setFinalResult(result);
      setStep("result");
    } catch (error) {
      console.error("Failed to submit enhanced quiz:", error);
      alert("提交失败，请稍后重试");
    } finally {
      setEnhancedLoading(false);
    }
  }, [
    courseId,
    selectedSectionId,
    enhancedAnswers,
    enhancedSessionIdRef,
    setStep,
  ]);

  const handleNextEnhancedQuestion = useCallback(
    async () => {
      if (currentQuestionIndex < enhancedQuestions.length - 1) {
        setCurrentQuestionIndex((prev) => prev + 1);
        setSubmitted(false);
      } else if (
        generationStatus === "completed" ||
        enhancedQuestions.length >= generationProgress.total
      ) {
        await handleSubmitAllEnhancedAnswers();
      }
    },
    [
      enhancedQuestions,
      generationStatus,
      generationProgress,
      setCurrentQuestionIndex,
      setSubmitted,
      handleSubmitAllEnhancedAnswers,
    ],
  );

  return {
    enhancedQuestions,
    setEnhancedQuestions,
    enhancedSessionIdRef,
    enhancedLoading,
    setEnhancedLoading,
    enhancedAnswers,
    setEnhancedAnswers,
    generationStatus,
    setGenerationStatus,
    generationProgress,
    setGenerationProgress,
    pollingIntervalRef,
    finalResult,
    setFinalResult,
    handleStartEnhancedQuiz,
    handleSubmitEnhancedAnswer,
    handleNextEnhancedQuestion,
    handleSubmitAllEnhancedAnswers,
  };
}
