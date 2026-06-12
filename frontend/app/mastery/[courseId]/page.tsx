"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  ChevronRight,
  CheckCircle,
  XCircle,
  Trophy,
  Target,
  Clock,
  Zap,
  AlertTriangle,
  Star,
  PartyPopper,
} from "lucide-react";
import { LazyMotion, domAnimation, m, AnimatePresence } from "framer-motion";
import { FavoriteButton } from "@/components/exercise/FavoriteButton";
import { NoteButton } from "@/components/exercise/NoteButton";
import { NoteEditor } from "@/components/notes/NoteEditor";
import { KnowledgeOrb } from "@/components/ui/knowledge-orb";
import { ExerciseSkeleton, GeneratingIndicator } from "@/components/exercise/ExerciseSkeleton";
import { staggerContainer, staggerItem, fadeIn, scaleIn } from "@/lib/animations";

import {
  getMasteryOverview,
  getSectionBaseQuestions,
  submitBaseAnswers,
  getStoredToken,
  logout,
  MASTERY_LEVEL_COLORS,
} from "@/lib/api";
import {
  saveMasteryExerciseProgress,
  completeMasteryQuiz,
  getMasteryChapterDetailProgress,
  getSectionMastery,
  type MasteryExerciseProgressItem,
} from "@/lib/api/learning-path";
import { collectWrongQuestion } from "@/lib/api/wrong-question";
import { getCourse } from "@/lib/api/courses";
import type {
  MasteryOverviewResponse,
  CourseDetailResponse,
  MasteryLevel,
  BaseQuestionResponse,
  BaseAnswersSubmitResponse,
  EnhancedQuizQuestion,
  EnhancedQuizSubmitResponse,
} from "@/types/api";
import { type MasteryStep, getQuestionType, DIFFICULTY_COLORS } from "./types";
import { useMasterySession } from "./use-mastery-session";
import { useBaseQuiz } from "./use-base-quiz";
import { useEnhancedQuiz } from "./use-enhanced-quiz";

export const metadata = {
  title: '精进之路 - 智码领航',
  description: '课程精进学习与测试',
}

function MasteryPathContent() {
  const params = useParams();
  const { push, replace } = useRouter();
  const searchParams = useSearchParams()
  // react-doctor-disable-next-line react-compiler-destructure-method, react-doctor/react-compiler-destructure-method
  const getSearchParam = (name: string) => searchParams.get(name)
  const courseId = Number(params.courseId);

  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<MasteryOverviewResponse | null>(
    null,
  );
  const [courseDetail, setCourseDetail] = useState<CourseDetailResponse | null>(
    null,
  );

  // Chapter selection state
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(
    null,
  );
  const [selectedChapterTitle, setSelectedChapterTitle] = useState<string>("");
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null); // 当前学习的小节
  const [step, setStep] = useState<MasteryStep>("select_chapter");

  // Base quiz state
  const [baseQuestions, setBaseQuestions] = useState<BaseQuestionResponse[]>(
    [],
  );
  const [baseQuestionLoading, setBaseQuestionLoading] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const {
    baseAnswers,
    setBaseAnswers,
    submitted,
    setSubmitted,
    isCorrect,
    setIsCorrect,
    completedQuestionsMap,
    setCompletedQuestionsMap,
    checkAnswer,
    restoreSubmitState,
  } = useBaseQuiz();

  // Analysis state
  const [baseResult, setBaseResult] =
    useState<BaseAnswersSubmitResponse | null>(null);



  const {
    startTrackedSession,
    endTrackedSession,
    currentSectionIdRef,
  } = useMasterySession(getSearchParam);

  const {
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
  } = useEnhancedQuiz(
    courseId,
    selectedChapterId,
    selectedSectionId,
    currentSectionIdRef,
    baseResult,
    currentQuestionIndex,
    setStep,
    setCurrentQuestionIndex,
    setSubmitted,
    setIsCorrect,
    setCompletedQuestionsMap,
  );

  // Note editor state
  const [showNoteEditor, setShowNoteEditor] = useState(false);
  const [editingNote, setEditingNote] = useState<import('@/types/api').NoteResponse | null>(null);
  const [noteRefreshKey, setNoteRefreshKey] = useState(0);

  const fetchOverview = useCallback(async () => {
    const token = getStoredToken();

    if (token) {
      // 已登录：获取掌握度数据
      try {
        const data = await getMasteryOverview(courseId, token);
        setOverview(data);
      } catch (error) {
        console.error("Failed to fetch mastery overview:", error);
      }
    }

    // 未登录也获取课程详情（公开接口）用于展示章节列表
    try {
      const detail = await getCourse(courseId);
      setCourseDetail(detail);
    } catch (error) {
      console.error("Failed to fetch course detail:", error);
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  // Handle query params for jump from wrong question book or section learning
  useEffect(() => {
    const chapterParam = getSearchParam("chapter");
    const sectionParam = getSearchParam("section");
    const exerciseParam = getSearchParam("exercise");


    // 如果没有必要的参数，不处理
    if (!chapterParam) {
      return;
    }

    if (!overview?.chapters) {
      return;
    }

    const chapterId = parseInt(chapterParam);
    const chapter = overview.chapters.find((c) => c.chapter_id === chapterId);


    if (!chapter) {
      return;
    }

    // 保存 section_id（如果有）
    const sectionId = sectionParam ? parseInt(sectionParam) : null;

    // 跳转到具体题目
    // exerciseParam 是 question_id，需要在获取题目列表后找到对应索引
    const targetQuestionId = exerciseParam ? parseInt(exerciseParam) : 0;

    // Directly start quiz at the target question
    startQuizAtQuestion(chapterId, targetQuestionId, sectionId || undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, overview]);



  // Start base quiz at a specific question (for jump from wrong question book)
  // targetQuestionId: 目标题目的 question_id，如果为 0 则从头开始或恢复进度
  const startQuizAtQuestion = async (
    chapterId: number,
    targetQuestionId: number = 0,
    sectionId?: number,
  ) => {
    const token = getStoredToken();
    if (!token) return;

    // 必须有 sectionId 才能获取题目
    if (!sectionId) {
      console.error("[精进之路] startQuizAtQuestion: sectionId is required");
      alert("请先选择小节");
      return;
    }

    await startTrackedSession(chapterId);
    setSelectedChapterId(chapterId);
    setSelectedSectionId(sectionId);
    currentSectionIdRef.current = sectionId; // 保存到 ref，避免 state 丢失

    // Set chapter title from overview
    const chapter = overview?.chapters?.find(c => c.chapter_id === chapterId);
    if (chapter) {
      setSelectedChapterTitle(chapter.title);
    }

    setBaseQuestionLoading(true);

    try {
      // 获取小节题目
      const data = await getSectionBaseQuestions(sectionId, token);
      if (data.questions.length > 0) {
      }
      setBaseQuestions(data.questions);

      // 获取章节进度（用于恢复答案状态）
      const progressData = await getMasteryChapterDetailProgress(
        courseId,
        chapterId,
        token
      ).catch(() => null);

      // 构建进度映射并恢复答案和完成状态
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
      setBaseAnswers(restoredAnswers);
      setCompletedQuestionsMap(completedMap);

      // 检查是否所有基础题都已完成（且不是从错题本跳转）
      const allCompleted = data.questions.every((q) => completedMap.has(q.id));
      if (allCompleted && targetQuestionId === 0) {
        // 所有基础题都完成了，计算结果并直接跳到分析界面
        let correctCount = 0;
        for (const q of data.questions) {
          if (completedMap.get(q.id)) {
            correctCount++;
          }
        }

        // 优先使用 BKT 掌握度分类知识点，兜底用简单统计
        let weakPoints: string[] = [];
        let strongPoints: string[] = [];
        try {
          const sectionMastery = await getSectionMastery(selectedSectionId!, token);
          const kpMasteries = sectionMastery.knowledge_points || [];
          const allKps = new Set<string>();
          for (const q of data.questions) {
            for (const kp of q.knowledge_points || []) {
              allKps.add(kp);
            }
          }
          const bktKps = new Map(kpMasteries.map((m: any) => [m.name, m]));
          // 预构建知识点到问题的索引
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
              // 无 BKT 数据，简单统计兜底
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
          // BKT 接口失败，兜底简单统计
          const kpStats = new Map<string, { correct: number; wrong: number }>();
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

        setBaseResult({
          section_id: selectedSectionId ?? 0,
          total_questions: data.questions.length,
          correct_answers: correctCount,
          accuracy: correctCount / data.questions.length,
          results: [],
          weak_points: weakPoints,
          strong_points: strongPoints,
          xp_earned: 0,
        });
        setStep("analysis");
        return;
      }

      // 不是全部完成，进入答题界面
      setStep("base_quiz");

      // 根据 targetQuestionId 找到正确的题目索引
      let startIndex = 0;
      if (targetQuestionId > 0) {
        // 从错题本跳转，找到该 question_id 对应的索引
        const foundIndex = data.questions.findIndex(
          (q) => q.id === targetQuestionId,
        );
        if (foundIndex >= 0) {
          startIndex = foundIndex;
        }
      } else {
        // 正常进入，检查是否有进度可恢复
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

      setCurrentQuestionIndex(startIndex);

      // 恢复起始题目的提交状态
      const startQuestion = data.questions[startIndex];
      if (startQuestion) {
        restoreSubmitState(startQuestion.id, completedMap);
      }

    } catch (error) {
      console.error("Failed to fetch base questions:", error);
      alert("加载测试题失败，请稍后重试");
      setStep("select_chapter");
    } finally {
      setBaseQuestionLoading(false);
    }
  };

  // Handle chapter selection - navigate to section selection page
  const handleSelectChapter = async (
    chapterId: number,
    chapterTitle: string,
  ) => {
    const token = getStoredToken();
    if (!token) {
      push('/login');
      return;
    }

    // Store chapter info for section page
    try {
      localStorage.setItem('current_chapter_info:v1', JSON.stringify({
        id: chapterId,
        title: chapterTitle,
        course_id: courseId,
        course_name: overview?.chapters[0]?.title || ''
      }));
    } catch (e) {
      // localStorage save failed, ignore
    }

    // Navigate to section selection page
    push(`/mastery/${courseId}/chapter/${chapterId}`);
  };

  // Start base quiz after viewing knowledge
  // targetQuestionId: 目标题目的 question_id，如果为 0 则从头开始或恢复进度
  const handleStartBaseQuiz = async (targetQuestionId: number = 0) => {
    const token = getStoredToken();
    if (!token || !selectedSectionId) return;

    setBaseQuestionLoading(true);

    try {
      // 获取小节题目
      const data = await getSectionBaseQuestions(selectedSectionId, token);
      setBaseQuestions(data.questions);

      // 获取章节进度（用于恢复答案状态）
      const progressData = selectedChapterId ? await getMasteryChapterDetailProgress(
        courseId,
        selectedChapterId,
        token,
      ).catch(() => null) : null;

      // 构建进度映射
      const progressMap = new Map<number, MasteryExerciseProgressItem>();
      if (progressData?.progress_items) {
        for (const item of progressData.progress_items) {
          progressMap.set(item.question_id, item);
        }
      }

      // 恢复答案状态和完成状态
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
      setBaseAnswers(restoredAnswers);
      setCompletedQuestionsMap(completedMap);

      // 检查是否所有基础题都已完成（且不是从错题本跳转）
      const allCompleted = data.questions.every((q) => completedMap.has(q.id));
      if (allCompleted && targetQuestionId === 0) {
        // 所有基础题都完成了，计算结果并直接跳到分析界面
        let correctCount = 0;
        for (const q of data.questions) {
          if (completedMap.get(q.id)) {
            correctCount++;
          }
        }

        // 优先使用 BKT 掌握度分类知识点，兜底用简单统计
        let weakPoints: string[] = [];
        let strongPoints: string[] = [];
        try {
          const sectionMastery = await getSectionMastery(selectedSectionId!, token);
          const kpMasteries = sectionMastery.knowledge_points || [];
          const allKps = new Set<string>();
          for (const q of data.questions) {
            for (const kp of q.knowledge_points || []) {
              allKps.add(kp);
            }
          }
          const bktKps = new Map(kpMasteries.map((m: any) => [m.name, m]));
          // 预构建知识点到问题的索引
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
              // 无 BKT 数据，简单统计兜底
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
          // BKT 接口失败，兜底简单统计
          const kpStats = new Map<string, { correct: number; wrong: number }>();
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

        setBaseResult({
          section_id: selectedSectionId ?? 0,
          total_questions: data.questions.length,
          correct_answers: correctCount,
          accuracy: correctCount / data.questions.length,
          results: [],
          weak_points: weakPoints,
          strong_points: strongPoints,
          xp_earned: 0,
        });
        setStep("analysis");
        return;
      }

      // 不是全部完成，进入答题界面
      setStep("base_quiz");

      // 确定起始题目索引
      let startIndex = 0;
      if (targetQuestionId > 0) {
        // 指定了目标题目 ID，找到对应索引
        const foundIndex = data.questions.findIndex(
          (q) => q.id === targetQuestionId,
        );
        if (foundIndex >= 0) {
          startIndex = foundIndex;
        }
      } else {
        // 正常进入，检查是否有进度可恢复
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

      setCurrentQuestionIndex(startIndex);

      // 恢复起始题目的提交状态
      const startQuestion = data.questions[startIndex];
      if (startQuestion) {
        restoreSubmitState(startQuestion.id, completedMap);
      }
    } catch (error) {
      console.error("Failed to fetch base questions:", error);
      alert("加载测试题失败，请稍后重试");
      setStep("select_chapter");
    } finally {
      setBaseQuestionLoading(false);
    }
  };

  // Handle base answer submission
  const handleSubmitBaseAnswer = async () => {
    const currentQuestion = baseQuestions[currentQuestionIndex];
    const answer = baseAnswers.get(currentQuestion.id);
    if (!answer) return;

    const correct = checkAnswer(currentQuestion, answer);
    const questionType = getQuestionType(currentQuestion);

    setIsCorrect(correct);
    setSubmitted(true);

    // 更新完成状态映射
    setCompletedQuestionsMap((prev) => {
      const newMap = new Map(prev);
      newMap.set(currentQuestion.id, correct);
      return newMap;
    });

    // Save progress to backend
    const token = getStoredToken();
    if (token && selectedChapterId) {
      try {
        const exerciseKey = `mastery-${courseId}-${selectedChapterId}-${currentQuestion.id}`;
        const sectionIdToSave = selectedSectionId ?? currentSectionIdRef.current ?? undefined;
        await saveMasteryExerciseProgress(
          {
            course_id: courseId,
            chapter_id: selectedChapterId,
            section_id: sectionIdToSave,
            question_id: currentQuestion.id,
            question_index: currentQuestionIndex + 1,
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

    // Collect wrong question if incorrect
    if (!correct) {
      if (token && selectedChapterId) {
        try {
          // Use question ID as exercise_key
          const exerciseKey = `mastery-${courseId}-${selectedChapterId}-${currentQuestion.id}`;
          await collectWrongQuestion(token, {
            exercise_key: exerciseKey,
            user_answer: answer,
            course_id: courseId,
            chapter_id: selectedChapterId,
            section_id: selectedSectionId ?? undefined,
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
  };

  // Move to next question or submit all
  const handleNextQuestion = async () => {
    if (currentQuestionIndex < baseQuestions.length - 1) {
      const nextIndex = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIndex);

      // 检查下一题是否已经完成，如果是则恢复提交状态
      const nextQuestion = baseQuestions[nextIndex];
      if (nextQuestion) {
        restoreSubmitState(nextQuestion.id, completedQuestionsMap);
      }
    } else {
      // Submit all answers
      await handleSubmitAllBaseAnswers();
    }
  };

  // Submit all base answers and get analysis
  const handleSubmitAllBaseAnswers = async () => {
    const token = getStoredToken();
    if (!token || !selectedChapterId || !selectedSectionId) {
      console.error("[精进之路] handleSubmitAllBaseAnswers: 缺少必要参数", { selectedChapterId, selectedSectionId });
      return;
    }

    setBaseQuestionLoading(true);

    try {
      const answersArray = Array.from(baseAnswers.entries()).map(
        ([questionId, answer]) => ({
          question_id: questionId,
          answer,
          time_spent: 30,
        }),
      );

      const result = await submitBaseAnswers(
        courseId,
        selectedChapterId,
        { section_id: selectedSectionId, answers: answersArray },
        token,
      );
      setBaseResult(result);

      // Update ChapterMastery with quiz completion
      if (selectedChapterId) {
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
              chapter_id: selectedChapterId,
              results: resultsForCompletion,
            },
            token,
          );
        } catch (error) {
          console.error("[精进之路] 章节进度更新失败:", error);
        }
      }

      setStep("analysis");
    } catch (error) {
      console.error("Failed to submit base answers:", error);
      alert("提交失败，请稍后重试");
    } finally {
      setBaseQuestionLoading(false);
    }
  };


  // 使用 isMountedRef 来区分 StrictMode 的假 unmount 和真正的 unmount
  const isMountedRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      // 如果很快重新 mount，则 isMountedRef 会变回 true
      isMountedRef.current = false;

      // 延迟执行 endTrackedSession，给 StrictMode 重新 mount 的机会
      requestAnimationFrame(() => {
        if (!isMountedRef.current) {
          void endTrackedSession();
        } else {
        }
      });
    };
  }, [endTrackedSession]);

  // Back to chapter selection
  const handleBackToChapters = async () => {
    await endTrackedSession();
    setStep("select_chapter");
    setSelectedChapterId(null);
    setSelectedSectionId(null); // 清除小节状态
    setBaseQuestions([]);
    setBaseAnswers(new Map());
    setCompletedQuestionsMap(new Map());
    setBaseResult(null);
    setEnhancedQuestions([]);
    setEnhancedAnswers(new Map());
    setFinalResult(null);

    // Check if we came from a section (小节)
    const fromSection = getSearchParam("fromSection");
    const chapterParam = getSearchParam("chapter");

    if (fromSection && chapterParam) {
      // Came from section learning page, return to the section learning page
      replace(`/mastery/${courseId}/chapter/${chapterParam}/section/${fromSection}`, { scroll: false });
    } else if (getSearchParam("chapter") || getSearchParam("exercise") || getSearchParam("skip")) {
      // Came from wrong question book or favorites, return to chapter selection
      replace(`/mastery/${courseId}`, { scroll: false });
    }

    fetchOverview();
  };

  // Loading state - only show for select_chapter step
  if (loading && step === "select_chapter") {
    return (
      <LazyMotion features={domAnimation}>
      <div className="min-h-screen bg-background flex items-center justify-center">
        <m.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <Loader2 className="size-16 text-primary mx-auto mb-4" strokeWidth={1.5} />
          <p className="text-muted-foreground">加载中...</p>
        </m.div>
      </div>
      </LazyMotion>
    );
  }

  // Result state
  if (step === "result" && finalResult) {
    return <ResultView finalResult={finalResult} onBackToChapters={handleBackToChapters} />;
  }

  // 查看题目（从分析界面返回题目列表）
  const handleViewQuestions = () => {
    // 跳转到最后一道题
    if (baseQuestions.length > 0) {
      setCurrentQuestionIndex(baseQuestions.length - 1);
      const lastQuestion = baseQuestions[baseQuestions.length - 1];
      if (lastQuestion && completedQuestionsMap.has(lastQuestion.id)) {
        setSubmitted(true);
        setIsCorrect(completedQuestionsMap.get(lastQuestion.id) || false);
      } else {
        setSubmitted(false);
        setIsCorrect(false);
      }
      setStep("base_quiz");
    }
  };

  // Analysis state - show weak points and offer enhanced quiz
  if (step === "analysis" && baseResult) {
    return (
      <AnalysisView
        baseResult={baseResult}
        enhancedLoading={enhancedLoading}
        onViewQuestions={handleViewQuestions}
        onBackToChapters={handleBackToChapters}
        onStartEnhancedQuiz={handleStartEnhancedQuiz}
      />
    );
  }

  // Enhanced quiz state
  if (step === "enhanced_quiz" && enhancedQuestions.length > 0) {
    return (
      <EnhancedQuizView
        enhancedQuestions={enhancedQuestions}
        currentQuestionIndex={currentQuestionIndex}
        enhancedAnswers={enhancedAnswers}
        enhancedLoading={enhancedLoading}
        generationStatus={generationStatus}
        generationProgress={generationProgress}
        submitted={submitted}
        isCorrect={isCorrect}
        setEnhancedAnswers={setEnhancedAnswers}
        onSubmit={handleSubmitEnhancedAnswer}
        onNext={handleNextEnhancedQuestion}
        onBackToChapters={handleBackToChapters}
      />
    );
  }

  // Base quiz state
  if (step === "base_quiz" && baseQuestions.length > 0) {
    return (
      <BaseQuizView
        baseQuestions={baseQuestions}
        currentQuestionIndex={currentQuestionIndex}
        baseAnswers={baseAnswers}
        submitted={submitted}
        isCorrect={isCorrect}
        completedQuestionsMap={completedQuestionsMap}
        baseQuestionLoading={baseQuestionLoading}
        selectedChapterTitle={selectedChapterTitle}
        courseId={courseId}
        selectedChapterId={selectedChapterId}
        selectedSectionId={selectedSectionId}
        noteRefreshKey={noteRefreshKey}
        showNoteEditor={showNoteEditor}
        editingNote={editingNote}
        setBaseAnswers={setBaseAnswers}
        setCurrentQuestionIndex={setCurrentQuestionIndex}
        setSubmitted={setSubmitted}
        setIsCorrect={setIsCorrect}
        setShowNoteEditor={setShowNoteEditor}
        setEditingNote={setEditingNote}
        setNoteRefreshKey={setNoteRefreshKey}
        onSubmit={handleSubmitBaseAnswer}
        onNext={handleNextQuestion}
        onBackToChapters={handleBackToChapters}
      />
    );
  }

  // Default: Chapter selection
  return (
    <ChapterListView
      overview={overview}
      courseDetail={courseDetail}
      onSelectChapter={handleSelectChapter}
      courseId={courseId}
      selectedChapterId={selectedChapterId}
      selectedSectionId={selectedSectionId}
      baseQuestions={baseQuestions}
      currentQuestionIndex={currentQuestionIndex}
      showNoteEditor={showNoteEditor}
      editingNote={editingNote}
      setShowNoteEditor={setShowNoteEditor}
      setEditingNote={setEditingNote}
      setNoteRefreshKey={setNoteRefreshKey}
      noteRefreshKey={noteRefreshKey}
    />
  );
}

// Wrapper with Suspense boundary for useSearchParams
import { Suspense } from "react"
import { Loader2 } from "lucide-react"
import { ResultView } from "./components/result-view";
import { AnalysisView } from "./components/analysis-view";
import { EnhancedQuizView } from "./components/enhanced-quiz-view";
import { BaseQuizView } from "./components/base-quiz-view";
import { ChapterListView } from "./components/chapter-list-view";

export default function MasteryPathPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="size-8 text-primary" strokeWidth={1.5} />
      </div>
    }>
      <MasteryPathContent />
    </Suspense>
  )
}
