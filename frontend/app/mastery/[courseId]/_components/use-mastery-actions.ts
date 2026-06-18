"use client";

import { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  getMasteryOverview,
  getSectionBaseQuestions,
  submitBaseAnswers,
  getStoredToken,
} from "@/lib/api";
import {
  saveMasteryExerciseProgress,
  completeMasteryQuiz,
  getMasteryChapterDetailProgress,
  getSectionMastery,
  type KnowledgePointMastery,
  type MasteryExerciseProgressItem,
} from "@/lib/api/learning-path";
import { collectWrongQuestion } from "@/lib/api/wrong-question";
import { getCourse } from "@/lib/api/courses";
import type {
  BaseAnswersSubmitResponse,
  BaseQuestionResponse,
  EnhancedQuizQuestion,
  EnhancedQuizSubmitResponse,
} from "@/types/api";
import type { MasteryPathSetters, MasteryPathState } from "./mastery-state";
import { getQuestionType } from "../types";

type BaseQuizContext = {
  baseAnswers: Map<number, string>;
  setBaseAnswers: React.Dispatch<
    React.SetStateAction<Map<number, string>>
  >;
  submitted: boolean;
  setSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
  isCorrect: boolean;
  setIsCorrect: React.Dispatch<React.SetStateAction<boolean>>;
  completedQuestionsMap: Map<number, boolean>;
  setCompletedQuestionsMap: React.Dispatch<
    React.SetStateAction<Map<number, boolean>>
  >;
  checkAnswer: (question: BaseQuestionResponse, answer: string) => boolean;
  restoreSubmitState: (questionId: number, map: Map<number, boolean>) => void;
};

type EnhancedQuizContext = {
  setEnhancedQuestions: (
    value:
      | EnhancedQuizQuestion[]
      | ((prev: EnhancedQuizQuestion[]) => EnhancedQuizQuestion[]),
  ) => void;
  setEnhancedAnswers: React.Dispatch<
    React.SetStateAction<Map<string, string>>
  >;
  setFinalResult: (
    value:
      | EnhancedQuizSubmitResponse
      | null
      | ((prev: EnhancedQuizSubmitResponse | null) => EnhancedQuizSubmitResponse | null),
  ) => void;
};

type SessionContext = {
  startTrackedSession: (chapterId: number) => Promise<void>;
  endTrackedSession: () => Promise<void>;
  currentSectionIdRef: React.MutableRefObject<number | null>;
};

export type MasteryActionDeps = {
  courseId: number;
  state: MasteryPathState;
  setters: MasteryPathSetters;
  searchParams: URLSearchParams;
  getSearchParam: (name: string) => string | null;
  session: SessionContext;
  baseQuiz: BaseQuizContext;
  enhancedQuiz: EnhancedQuizContext;
  refreshOverview: () => Promise<void>;
};

export type MasteryActionHandlers = {
  startQuizAtQuestion: (
    chapterId: number,
    targetQuestionId?: number,
    sectionId?: number,
  ) => Promise<void>;
  handleStartBaseQuiz: (targetQuestionId?: number) => Promise<void>;
  handleSubmitBaseAnswer: () => Promise<void>;
  handleNextQuestion: () => Promise<void>;
  handleSubmitAllBaseAnswers: () => Promise<void>;
  handleBackToChapters: () => Promise<void>;
  handleSelectChapter: (
    chapterId: number,
    chapterTitle: string,
  ) => Promise<void>;
  handleViewQuestions: () => void;
};

export function useMasteryActions(deps: MasteryActionDeps): MasteryActionHandlers {
  const { push, replace } = useRouter();
  const {
    courseId,
    state,
    setters,
    searchParams,
    getSearchParam,
    session,
    baseQuiz,
    enhancedQuiz,
    refreshOverview,
  } = deps;

  const startQuizAtQuestion = useCallback(
    async (
      chapterId: number,
      targetQuestionId: number = 0,
      sectionId?: number,
    ) => {
      const token = getStoredToken();
      if (!token) return;

      if (!sectionId) {
        console.error("[精进之路] startQuizAtQuestion: sectionId is required");
        alert("请先选择小节");
        return;
      }

      await session.startTrackedSession(chapterId);
      setters.setSelectedChapterId(chapterId);
      setters.setSelectedSectionId(sectionId);
      session.currentSectionIdRef.current = sectionId;

      const chapter = state.overview?.chapters?.find(
        (c) => c.chapter_id === chapterId,
      );
      if (chapter) {
        setters.setSelectedChapterTitle(chapter.title);
      }

      setters.setBaseQuestionLoading(true);

      try {
        const data = await getSectionBaseQuestions(sectionId, token);
        setters.setBaseQuestions(data.questions);

        const progressData = await getMasteryChapterDetailProgress(
          courseId,
          chapterId,
          token,
        ).catch(() => null);

        const restoredAnswers = new Map<number, string>();
        const completedMap = new Map<number, boolean>();
        if (progressData?.progress_items) {
          for (const item of progressData.progress_items) {
            if (item.user_answer) {
              restoredAnswers.set(item.question_id, item.user_answer);
            }
            if (item.is_completed) {
              completedMap.set(item.question_id, item.is_correct);
            }
          }
        }
        baseQuiz.setBaseAnswers(restoredAnswers);
        baseQuiz.setCompletedQuestionsMap(completedMap);

        const allCompleted = data.questions.every((q) => completedMap.has(q.id));
        if (allCompleted && targetQuestionId === 0) {
          let correctCount = 0;
          for (const q of data.questions) {
            if (completedMap.get(q.id)) {
              correctCount++;
            }
          }

          const weakPoints: string[] = [];
          const strongPoints: string[] = [];
          try {
            const sectionMastery = await getSectionMastery(
              state.selectedSectionId!,
              token,
            );
            const kpMasteries = sectionMastery.knowledge_points || [];
            const allKps = new Set<string>();
            for (const q of data.questions) {
              for (const kp of q.knowledge_points || []) {
                allKps.add(kp);
              }
            }
            const bktKps = new Map<string, KnowledgePointMastery>(
              kpMasteries.map((mastery) => [mastery.name, mastery]),
            );
            const kpToQuestions = new Map<string, typeof data.questions>();
            for (const q of data.questions) {
              for (const kp of q.knowledge_points || []) {
                if (!kpToQuestions.has(kp)) kpToQuestions.set(kp, []);
                kpToQuestions.get(kp)!.push(q);
              }
            }
            for (const kp of allKps) {
              const bktKp = bktKps.get(kp);
              if (bktKp && bktKp.total_attempts > 0) {
                if (bktKp.is_mastered) {
                  strongPoints.push(kp);
                } else {
                  weakPoints.push(kp);
                }
              } else {
                let kpCorrect = 0;
                let kpWrong = 0;
                const questionsForKp = kpToQuestions.get(kp) || [];
                for (const q of questionsForKp) {
                  if (completedMap.get(q.id)) {
                    kpCorrect++;
                  } else {
                    kpWrong++;
                  }
                }
                if (kpWrong >= kpCorrect) {
                  weakPoints.push(kp);
                } else {
                  strongPoints.push(kp);
                }
              }
            }
          } catch {
            const kpStats = new Map<
              string,
              { correct: number; wrong: number }
            >();
            for (const q of data.questions) {
              const isCorrect = completedMap.get(q.id);
              for (const kp of q.knowledge_points || []) {
                const s = kpStats.get(kp) || { correct: 0, wrong: 0 };
                if (isCorrect) s.correct++;
                else s.wrong++;
                kpStats.set(kp, s);
              }
            }
            for (const [kp, stats] of kpStats) {
              if (stats.wrong >= stats.correct) weakPoints.push(kp);
              else strongPoints.push(kp);
            }
          }

          const baseResult: BaseAnswersSubmitResponse = {
            section_id: state.selectedSectionId ?? 0,
            total_questions: data.questions.length,
            correct_answers: correctCount,
            accuracy: correctCount / data.questions.length,
            results: [],
            weak_points: weakPoints,
            strong_points: strongPoints,
            xp_earned: 0,
          };
          setters.setBaseResult(baseResult);
          setters.setStep("analysis");
          return;
        }

        setters.setStep("base_quiz");

        let startIndex = 0;
        if (targetQuestionId > 0) {
          const foundIndex = data.questions.findIndex(
            (q) => q.id === targetQuestionId,
          );
          if (foundIndex >= 0) {
            startIndex = foundIndex;
          }
        } else {
          const progressMap = new Map(
            progressData?.progress_items?.map((p) => [p.question_id, p]) || [],
          );
          let firstUncompletedIndex = -1;
          for (let i = 0; i < data.questions.length; i++) {
            const q = data.questions[i];
            const progress = progressMap.get(q.id);
            if (!progress?.is_completed && firstUncompletedIndex === -1) {
              firstUncompletedIndex = i;
            }
          }
          if (firstUncompletedIndex >= 0) {
            startIndex = firstUncompletedIndex;
          }
        }

        setters.setCurrentQuestionIndex(startIndex);

        const startQuestion = data.questions[startIndex];
        if (startQuestion) {
          baseQuiz.restoreSubmitState(startQuestion.id, completedMap);
        }
      } catch (error) {
        console.error("Failed to fetch base questions:", error);
        alert("加载测试题失败，请稍后重试");
        setters.setStep("select_chapter");
      } finally {
        setters.setBaseQuestionLoading(false);
      }
    },
    [courseId, state.overview, state.selectedSectionId, session, baseQuiz, setters],
  );

  const startQuizAtQuestionRef = useRef(startQuizAtQuestion);
  startQuizAtQuestionRef.current = startQuizAtQuestion;

  // Handle query params for jump from wrong question book or section learning
  useEffect(() => {
    const chapterParam = searchParams.get("chapter");
    const sectionParam = searchParams.get("section");
    const exerciseParam = searchParams.get("exercise");

    if (!chapterParam) return;
    if (!state.overview?.chapters) return;

    const chapterId = parseInt(chapterParam);
    const chapter = state.overview.chapters.find(
      (c) => c.chapter_id === chapterId,
    );
    if (!chapter) return;

    const sectionId = sectionParam ? parseInt(sectionParam) : null;
    const targetQuestionId = exerciseParam ? parseInt(exerciseParam) : 0;

    void startQuizAtQuestionRef.current(
      chapterId,
      targetQuestionId,
      sectionId || undefined,
    );
  }, [searchParams, state.overview]);

  const handleSelectChapter = useCallback(
    async (chapterId: number, chapterTitle: string) => {
      const token = getStoredToken();
      if (!token) {
        push("/login");
        return;
      }

      try {
        localStorage.setItem(
          "current_chapter_info:v1",
          JSON.stringify({
            id: chapterId,
            title: chapterTitle,
            course_id: courseId,
            course_name: state.overview?.chapters[0]?.title || "",
          }),
        );
      } catch (e) {
        // localStorage save failed, ignore
      }

      push(`/mastery/${courseId}/chapter/${chapterId}`);
    },
    [courseId, push, state.overview],
  );

  const handleStartBaseQuiz = useCallback(
    async (targetQuestionId: number = 0) => {
      const token = getStoredToken();
      if (!token || !state.selectedSectionId) return;

      setters.setBaseQuestionLoading(true);

      try {
        const data = await getSectionBaseQuestions(state.selectedSectionId, token);
        setters.setBaseQuestions(data.questions);

        const progressData = state.selectedChapterId
          ? await getMasteryChapterDetailProgress(
              courseId,
              state.selectedChapterId,
              token,
            ).catch(() => null)
          : null;

        const progressMap = new Map<number, MasteryExerciseProgressItem>();
        if (progressData?.progress_items) {
          for (const item of progressData.progress_items) {
            progressMap.set(item.question_id, item);
          }
        }

        const restoredAnswers = new Map<number, string>();
        const completedMap = new Map<number, boolean>();
        for (let i = 0; i < data.questions.length; i++) {
          const q = data.questions[i];
          const progress = progressMap.get(q.id);
          if (progress?.user_answer) {
            restoredAnswers.set(q.id, progress.user_answer);
          }
          if (progress?.is_completed) {
            completedMap.set(q.id, progress.is_correct);
          }
        }
        baseQuiz.setBaseAnswers(restoredAnswers);
        baseQuiz.setCompletedQuestionsMap(completedMap);

        const allCompleted = data.questions.every((q) => completedMap.has(q.id));
        if (allCompleted && targetQuestionId === 0) {
          let correctCount = 0;
          for (const q of data.questions) {
            if (completedMap.get(q.id)) {
              correctCount++;
            }
          }

          const weakPoints: string[] = [];
          const strongPoints: string[] = [];
          try {
            const sectionMastery = await getSectionMastery(
              state.selectedSectionId!,
              token,
            );
            const kpMasteries = sectionMastery.knowledge_points || [];
            const allKps = new Set<string>();
            for (const q of data.questions) {
              for (const kp of q.knowledge_points || []) {
                allKps.add(kp);
              }
            }
            const bktKps = new Map<string, KnowledgePointMastery>(
              kpMasteries.map((mastery) => [mastery.name, mastery]),
            );
            const kpToQuestions = new Map<string, typeof data.questions>();
            for (const q of data.questions) {
              for (const kp of q.knowledge_points || []) {
                if (!kpToQuestions.has(kp)) kpToQuestions.set(kp, []);
                kpToQuestions.get(kp)!.push(q);
              }
            }
            for (const kp of allKps) {
              const bktKp = bktKps.get(kp);
              if (bktKp && bktKp.total_attempts > 0) {
                if (bktKp.is_mastered) {
                  strongPoints.push(kp);
                } else {
                  weakPoints.push(kp);
                }
              } else {
                let kpCorrect = 0;
                let kpWrong = 0;
                const questionsForKp = kpToQuestions.get(kp) || [];
                for (const q of questionsForKp) {
                  if (completedMap.get(q.id)) {
                    kpCorrect++;
                  } else {
                    kpWrong++;
                  }
                }
                if (kpWrong >= kpCorrect) {
                  weakPoints.push(kp);
                } else {
                  strongPoints.push(kp);
                }
              }
            }
          } catch {
            const kpStats = new Map<
              string,
              { correct: number; wrong: number }
            >();
            for (const q of data.questions) {
              const isCorrect = completedMap.get(q.id);
              for (const kp of q.knowledge_points || []) {
                const s = kpStats.get(kp) || { correct: 0, wrong: 0 };
                if (isCorrect) s.correct++;
                else s.wrong++;
                kpStats.set(kp, s);
              }
            }
            for (const [kp, stats] of kpStats) {
              if (stats.wrong >= stats.correct) weakPoints.push(kp);
              else strongPoints.push(kp);
            }
          }

          const baseResult: BaseAnswersSubmitResponse = {
            section_id: state.selectedSectionId ?? 0,
            total_questions: data.questions.length,
            correct_answers: correctCount,
            accuracy: correctCount / data.questions.length,
            results: [],
            weak_points: weakPoints,
            strong_points: strongPoints,
            xp_earned: 0,
          };
          setters.setBaseResult(baseResult);
          setters.setStep("analysis");
          return;
        }

        setters.setStep("base_quiz");

        let startIndex = 0;
        if (targetQuestionId > 0) {
          const foundIndex = data.questions.findIndex(
            (q) => q.id === targetQuestionId,
          );
          if (foundIndex >= 0) {
            startIndex = foundIndex;
          }
        } else {
          let firstUncompletedIndex = -1;
          let lastCompletedIndex = -1;

          for (let i = 0; i < data.questions.length; i++) {
            const q = data.questions[i];
            const progress = progressMap.get(q.id);

            if (!progress?.is_completed && firstUncompletedIndex === -1) {
              firstUncompletedIndex = i;
            }
            if (progress?.is_completed) {
              lastCompletedIndex = i;
            }
          }

          if (firstUncompletedIndex >= 0) {
            startIndex = firstUncompletedIndex;
          } else if (
            lastCompletedIndex >= 0 &&
            lastCompletedIndex < data.questions.length - 1
          ) {
            startIndex = lastCompletedIndex + 1;
          }
        }

        setters.setCurrentQuestionIndex(startIndex);

        const startQuestion = data.questions[startIndex];
        if (startQuestion) {
          baseQuiz.restoreSubmitState(startQuestion.id, completedMap);
        }
      } catch (error) {
        console.error("Failed to fetch base questions:", error);
        alert("加载测试题失败，请稍后重试");
        setters.setStep("select_chapter");
      } finally {
        setters.setBaseQuestionLoading(false);
      }
    },
    [
      courseId,
      state.selectedChapterId,
      state.selectedSectionId,
      baseQuiz,
      setters,
    ],
  );

  const handleSubmitAllBaseAnswers = useCallback(async () => {
    const token = getStoredToken();
    if (
      !token ||
      !state.selectedChapterId ||
      !state.selectedSectionId
    ) {
      console.error(
        "[精进之路] handleSubmitAllBaseAnswers: 缺少必要参数",
        {
          selectedChapterId: state.selectedChapterId,
          selectedSectionId: state.selectedSectionId,
        },
      );
      return;
    }

    setters.setBaseQuestionLoading(true);

    try {
      const answersArray = Array.from(baseQuiz.baseAnswers.entries()).map(
        ([questionId, answer]) => ({
          question_id: questionId,
          answer,
          time_spent: 30,
        }),
      );

      const result = await submitBaseAnswers(
        courseId,
        state.selectedChapterId,
        { section_id: state.selectedSectionId, answers: answersArray },
        token,
      );
      setters.setBaseResult(result);

      if (state.selectedChapterId) {
        const resultsForCompletion = result.results.map((r) => ({
          question_id: r.question_id,
          is_correct: r.is_correct,
          user_answer: r.user_answer,
          correct_answer: r.correct_answer,
        }));

        try {
          await completeMasteryQuiz(
            {
              course_id: courseId,
              chapter_id: state.selectedChapterId,
              results: resultsForCompletion,
            },
            token,
          );
        } catch (error) {
          console.error("[精进之路] 章节进度更新失败:", error);
        }
      }

      setters.setStep("analysis");
    } catch (error) {
      console.error("Failed to submit base answers:", error);
      alert("提交失败，请稍后重试");
    } finally {
      setters.setBaseQuestionLoading(false);
    }
  }, [
    courseId,
    state.selectedChapterId,
    state.selectedSectionId,
    baseQuiz.baseAnswers,
    setters,
  ]);

  // Forward ref so handleNextQuestion can reference handleSubmitAllBaseAnswers
  // without a TDZ issue at hook declaration time.
  const submitAllRef = useRef(handleSubmitAllBaseAnswers);
  submitAllRef.current = handleSubmitAllBaseAnswers;

  const handleSubmitBaseAnswer = useCallback(async () => {
    const currentQuestion = state.baseQuestions[state.currentQuestionIndex];
    const answer = baseQuiz.baseAnswers.get(currentQuestion.id);
    if (!answer) return;

    const correct = baseQuiz.checkAnswer(currentQuestion, answer);
    const questionType = getQuestionType(currentQuestion);

    baseQuiz.setSubmitted(true);
    baseQuiz.setIsCorrect(correct);

    baseQuiz.setCompletedQuestionsMap((prev) => {
      const newMap = new Map(prev);
      newMap.set(currentQuestion.id, correct);
      return newMap;
    });

    const token = getStoredToken();
    if (token && state.selectedChapterId) {
      try {
        const exerciseKey = `mastery-${courseId}-${state.selectedChapterId}-${currentQuestion.id}`;
        const sectionIdToSave =
          state.selectedSectionId ??
          session.currentSectionIdRef.current ??
          undefined;
        await saveMasteryExerciseProgress(
          {
            course_id: courseId,
            chapter_id: state.selectedChapterId,
            section_id: sectionIdToSave,
            question_id: currentQuestion.id,
            question_index: state.currentQuestionIndex + 1,
            question_type: "base",
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
        console.error("[精进之路] 进度保存失败:", error);
      }
    }

    if (!correct) {
      if (token && state.selectedChapterId) {
        try {
          const exerciseKey = `mastery-${courseId}-${state.selectedChapterId}-${currentQuestion.id}`;
          await collectWrongQuestion(token, {
            exercise_key: exerciseKey,
            user_answer: answer,
            course_id: courseId,
            chapter_id: state.selectedChapterId,
            section_id: state.selectedSectionId ?? undefined,
            exercise_content: {
              text: currentQuestion.text,
              options: currentQuestion.options,
              type: questionType,
            },
            exercise_type: questionType,
            knowledge_points: currentQuestion.knowledge_points || [],
          });
        } catch (error) {
          console.error("[精进之路] 错题收集失败:", error);
        }
      }
    }
  }, [
    courseId,
    state.baseQuestions,
    state.currentQuestionIndex,
    state.selectedChapterId,
    state.selectedSectionId,
    baseQuiz,
    session.currentSectionIdRef,
  ]);

  const handleNextQuestion = useCallback(async () => {
    if (state.currentQuestionIndex < state.baseQuestions.length - 1) {
      const nextIndex = state.currentQuestionIndex + 1;
      setters.setCurrentQuestionIndex(nextIndex);

      const nextQuestion = state.baseQuestions[nextIndex];
      if (nextQuestion) {
        baseQuiz.restoreSubmitState(nextQuestion.id, baseQuiz.completedQuestionsMap);
      }
    } else {
      await submitAllRef.current();
    }
  }, [
    state.baseQuestions,
    state.currentQuestionIndex,
    baseQuiz,
    setters,
  ]);

  // Use isMountedRef to distinguish StrictMode fake unmount vs real unmount
  const isMountedRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;

      requestAnimationFrame(() => {
        if (!isMountedRef.current) {
          void session.endTrackedSession();
        } else {
        }
      });
    };
  }, [session.endTrackedSession]);

  const handleBackToChapters = useCallback(async () => {
    await session.endTrackedSession();
    setters.setStep("select_chapter");
    setters.setSelectedChapterId(null);
    setters.setSelectedSectionId(null);
    setters.setBaseQuestions([]);
    baseQuiz.setBaseAnswers(new Map());
    baseQuiz.setCompletedQuestionsMap(new Map());
    setters.setBaseResult(null);
    enhancedQuiz.setEnhancedQuestions([]);
    enhancedQuiz.setEnhancedAnswers(new Map());
    enhancedQuiz.setFinalResult(null);

    const fromSection = getSearchParam("fromSection");
    const chapterParam = getSearchParam("chapter");

    if (fromSection && chapterParam) {
      replace(
        `/mastery/${courseId}/chapter/${chapterParam}/section/${fromSection}`,
        { scroll: false },
      );
    } else if (
      getSearchParam("chapter") ||
      getSearchParam("exercise") ||
      getSearchParam("skip")
    ) {
      replace(`/mastery/${courseId}`, { scroll: false });
    }

    await refreshOverview();
  }, [
    courseId,
    getSearchParam,
    replace,
    refreshOverview,
    session,
    baseQuiz,
    enhancedQuiz,
    setters,
  ]);

  const handleViewQuestions = useCallback(() => {
    if (state.baseQuestions.length > 0) {
      setters.setCurrentQuestionIndex(state.baseQuestions.length - 1);
      const lastQuestion = state.baseQuestions[state.baseQuestions.length - 1];
      if (
        lastQuestion &&
        baseQuiz.completedQuestionsMap.has(lastQuestion.id)
      ) {
        baseQuiz.setSubmitted(true);
        baseQuiz.setIsCorrect(
          baseQuiz.completedQuestionsMap.get(lastQuestion.id) || false,
        );
      } else {
        baseQuiz.setSubmitted(false);
        baseQuiz.setIsCorrect(false);
      }
      setters.setStep("base_quiz");
    }
  }, [state.baseQuestions, baseQuiz, setters]);

  return {
    startQuizAtQuestion: startQuizAtQuestionRef.current,
    handleStartBaseQuiz,
    handleSubmitBaseAnswer,
    handleNextQuestion,
    handleSubmitAllBaseAnswers,
    handleBackToChapters,
    handleSelectChapter,
    handleViewQuestions,
  };
}

// Helper hook used by useMasteryActions consumers to provide the
// refreshOverview callback that re-runs the initial overview fetch.
export function useRefreshOverview(
  courseId: number,
  setOverview: (value: import("@/types/api").MasteryOverviewResponse | null) => void,
  setCourseDetail: (
    value: import("@/types/api").CourseDetailResponse | null,
  ) => void,
  setLoading: (value: boolean) => void,
): () => Promise<void> {
  return useCallback(async () => {
    const token = getStoredToken();

    if (token) {
      try {
        const data = await getMasteryOverview(courseId, token);
        setOverview(data);
      } catch (error) {
        console.error("Failed to fetch mastery overview:", error);
      }
    }

    try {
      const detail = await getCourse(courseId);
      setCourseDetail(detail);
    } catch (error) {
      console.error("Failed to fetch course detail:", error);
    } finally {
      setLoading(false);
    }
  }, [courseId, setCourseDetail, setLoading, setOverview]);
}
