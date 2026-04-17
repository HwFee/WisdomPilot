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
} from "lucide-react";
import { FavoriteButton } from "@/components/exercise/FavoriteButton";

import {
  getMasteryOverview,
  getChapterBaseQuestions,
  submitBaseAnswers,
  generateEnhancedQuiz,
  submitEnhancedQuiz,
  getStoredToken,
  logout,
  MASTERY_LEVEL_COLORS,
  getChapterKnowledgeContent,
  startLearningSession,
  endLearningSession,
} from "@/lib/api";
import { endLearningSessionKeepalive } from "@/lib/api/stats";
import {
  saveMasteryExerciseProgress,
  completeMasteryQuiz,
  getMasteryChapterDetailProgress,
  type MasteryExerciseProgressItem,
} from "@/lib/api/learning-path";
import { collectWrongQuestion } from "@/lib/api/wrong-question";
import type {
  MasteryOverviewResponse,
  MasteryLevel,
  BaseQuestionResponse,
  BaseAnswersSubmitResponse,
  EnhancedQuizQuestion,
  EnhancedQuizSubmitResponse,
  KnowledgeContentResponse,
} from "@/types/api";

type MasteryStep =
  | "select_chapter"
  | "knowledge"
  | "base_quiz"
  | "analysis"
  | "enhanced_quiz"
  | "result";

// Helper function to get question type
const getQuestionType = (
  question: BaseQuestionResponse,
): "choice" | "programming" | "fill_blank" => {
  return question.question_type || question.type || "choice";
};

// Difficulty colors
const DIFFICULTY_COLORS: Record<number, string> = {
  1: "bg-green-500/20 text-green-400 border-green-500/30",
  2: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  3: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  4: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  5: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function MasteryPathPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const courseId = Number(params.courseId);

  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<MasteryOverviewResponse | null>(
    null,
  );

  // Chapter selection state
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(
    null,
  );
  const [selectedChapterTitle, setSelectedChapterTitle] = useState<string>("");
  const [step, setStep] = useState<MasteryStep>("select_chapter");

  // Base quiz state
  const [baseQuestions, setBaseQuestions] = useState<BaseQuestionResponse[]>(
    [],
  );
  const [baseQuestionLoading, setBaseQuestionLoading] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [baseAnswers, setBaseAnswers] = useState<Map<number, string>>(
    new Map(),
  );
  const [submitted, setSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  // Per-question completion tracking (question_id -> is_correct)
  // Used to restore submitted state when re-entering a chapter
  const [completedQuestionsMap, setCompletedQuestionsMap] = useState<
    Map<number, boolean>
  >(new Map());

  // Analysis state
  const [baseResult, setBaseResult] =
    useState<BaseAnswersSubmitResponse | null>(null);

  // Enhanced quiz state
  const [enhancedQuestions, setEnhancedQuestions] = useState<
    EnhancedQuizQuestion[]
  >([]);
  const [enhancedSessionId, setEnhancedSessionId] = useState<string>("");
  const [enhancedLoading, setEnhancedLoading] = useState(false);
  const [enhancedAnswers, setEnhancedAnswers] = useState<Map<string, string>>(
    new Map(),
  );

  // Final result state
  const [finalResult, setFinalResult] =
    useState<EnhancedQuizSubmitResponse | null>(null);

  // Knowledge content state
  const [knowledgeContent, setKnowledgeContent] =
    useState<KnowledgeContentResponse | null>(null);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);

  // Track whether the jump from wrong question book has been handled
  const jumpHandledRef = useRef(false);
  const sessionStartedAtRef = useRef<number | null>(null);
  const activeSessionChapterIdRef = useRef<number | null>(null);
  const isEndingSessionRef = useRef(false);

  const fetchOverview = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      logout();
      router.push("/login");
      return;
    }

    try {
      const data = await getMasteryOverview(courseId, token);
      setOverview(data);
    } catch (error) {
      console.error("Failed to fetch mastery overview:", error);
    } finally {
      setLoading(false);
    }
  }, [courseId, router]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  // Handle query params for jump from wrong question book
  useEffect(() => {
    // Only handle jump once — prevent re-triggering after exit
    if (jumpHandledRef.current) return;

    const chapterParam = searchParams.get("chapter");
    const exerciseParam = searchParams.get("exercise");
    const skipKnowledge = searchParams.get("skip") === "1";

    if (chapterParam && overview?.chapters) {
      const chapterId = parseInt(chapterParam);
      const chapter = overview.chapters.find((c) => c.chapter_id === chapterId);

      if (chapter) {
        // Mark as handled so it won't re-trigger after exit
        jumpHandledRef.current = true;

        // exerciseParam 是 question_id，需要在获取题目列表后找到对应索引
        const targetQuestionId = exerciseParam ? parseInt(exerciseParam) : 0;

        // Select the chapter
        handleSelectChapterForJump(
          chapterId,
          chapter.title,
          targetQuestionId,
          skipKnowledge,
        );
      }
    }
  }, [searchParams, overview]);

  const startTrackedSession = useCallback(async (chapterId: number) => {
    const token = getStoredToken();
    if (!token) return;

    if (
      activeSessionChapterIdRef.current === chapterId &&
      sessionStartedAtRef.current
    ) {
      return;
    }

    if (
      activeSessionChapterIdRef.current !== null &&
      sessionStartedAtRef.current
    ) {
      const prevChapterId = activeSessionChapterIdRef.current ?? undefined;
      const durationSeconds = Math.max(
        1,
        Math.floor((Date.now() - sessionStartedAtRef.current) / 1000),
      );
      activeSessionChapterIdRef.current = null;
      sessionStartedAtRef.current = null;
      try {
        // Await here since we're about to start a new session — must finish first
        await endLearningSession(token, durationSeconds, prevChapterId);
      } catch (error) {
        console.error("[精进之路] 结束上一段学习会话失败:", error);
      }
    }

    try {
      await startLearningSession(token, chapterId, 0);
      activeSessionChapterIdRef.current = chapterId;
      sessionStartedAtRef.current = Date.now();
    } catch (error) {
      console.error("[精进之路] 开始学习会话失败:", error);
    }
  }, []);

  const endTrackedSession = useCallback(async () => {
    const token = getStoredToken();
    if (!token || !sessionStartedAtRef.current || isEndingSessionRef.current)
      return;

    isEndingSessionRef.current = true;
    const chapterId = activeSessionChapterIdRef.current ?? undefined;
    const durationSeconds = Math.max(
      1,
      Math.floor((Date.now() - sessionStartedAtRef.current) / 1000),
    );
    activeSessionChapterIdRef.current = null;
    sessionStartedAtRef.current = null;
    isEndingSessionRef.current = false;

    // Use keepalive so the request survives page navigation / component unmount
    endLearningSessionKeepalive(token, durationSeconds, chapterId);
  }, []);

  // Handle chapter selection - load knowledge content first (with optional question ID for jump)
  const handleSelectChapterForJump = async (
    chapterId: number,
    chapterTitle: string,
    targetQuestionId: number = 0,
    skipKnowledge: boolean = false,
  ) => {
    const token = getStoredToken();
    if (!token) return;

    await startTrackedSession(chapterId);
    setSelectedChapterId(chapterId);
    setSelectedChapterTitle(chapterTitle);

    if (skipKnowledge) {
      // Skip knowledge step, go directly to quiz at specific question
      await startQuizAtQuestion(chapterId, targetQuestionId);
    } else {
      // Normal flow - show knowledge first
      setKnowledgeLoading(true);
      setStep("knowledge");

      try {
        const knowledgeData = await getChapterKnowledgeContent(
          courseId,
          chapterId,
          token,
        );
        setKnowledgeContent(knowledgeData);
      } catch (error) {
        console.error("Failed to fetch knowledge content:", error);
        setKnowledgeContent(null);
      } finally {
        setKnowledgeLoading(false);
      }
    }
  };

  // Start base quiz at a specific question (for jump from wrong question book)
  // targetQuestionId: 目标题目的 question_id，如果为 0 则从头开始或恢复进度
  const startQuizAtQuestion = async (
    chapterId: number,
    targetQuestionId: number = 0,
  ) => {
    const token = getStoredToken();
    if (!token) return;

    setBaseQuestionLoading(true);
    setStep("base_quiz");

    try {
      // 并行获取题目和进度
      const [data, progressData] = await Promise.all([
        getChapterBaseQuestions(courseId, chapterId, token),
        getMasteryChapterDetailProgress(courseId, chapterId, token).catch(
          () => null,
        ),
      ]);
      setBaseQuestions(data.questions);

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

      // 根据 targetQuestionId 找到正确的题目索引
      let startIndex = 0;
      if (targetQuestionId > 0) {
        // 从错题本跳转，找到该 question_id 对应的索引
        const foundIndex = data.questions.findIndex(
          (q) => q.id === targetQuestionId,
        );
        if (foundIndex >= 0) {
          startIndex = foundIndex;
          console.log(
            `[精进之路] 从错题本跳转: 找到题目 ID=${targetQuestionId}, 索引=${foundIndex + 1}`,
          );
        } else {
          console.warn(
            `[精进之路] 从错题本跳转: 未找到题目 ID=${targetQuestionId}，从头开始`,
          );
        }
      } else {
        // 正常进入，检查是否有进度可恢复
        let firstUncompletedIndex = -1;
        for (let i = 0; i < data.questions.length; i++) {
          const q = data.questions[i];
          const progress = progressData?.progress_items?.find(
            (p) => p.question_id === q.id,
          );
          if (!progress?.is_completed && firstUncompletedIndex === -1) {
            firstUncompletedIndex = i;
          }
        }
        if (firstUncompletedIndex >= 0) {
          startIndex = firstUncompletedIndex;
          console.log(
            `[精进之路] 恢复进度: 从第 ${firstUncompletedIndex + 1} 题继续`,
          );
        }
      }

      setCurrentQuestionIndex(startIndex);

      // 恢复起始题目的提交状态
      const startQuestion = data.questions[startIndex];
      if (startQuestion && completedMap.has(startQuestion.id)) {
        setSubmitted(true);
        setIsCorrect(completedMap.get(startQuestion.id) || false);
      } else {
        setSubmitted(false);
        setIsCorrect(false);
      }

      console.log(
        `[精进之路] 开始答题: 起始题目=${startIndex + 1}, 总题数=${data.questions.length}, 已恢复答案=${restoredAnswers.size}个, 已完成=${completedMap.size}个`,
      );
    } catch (error) {
      console.error("Failed to fetch base questions:", error);
      alert("加载测试题失败，请稍后重试");
      setStep("select_chapter");
    } finally {
      setBaseQuestionLoading(false);
    }
  };

  // Handle chapter selection - load knowledge content first
  const handleSelectChapter = async (
    chapterId: number,
    chapterTitle: string,
  ) => {
    const token = getStoredToken();
    if (!token) return;

    await startTrackedSession(chapterId);
    setSelectedChapterId(chapterId);
    setSelectedChapterTitle(chapterTitle);
    setKnowledgeLoading(true);
    setStep("knowledge");

    try {
      // First load knowledge content
      const knowledgeData = await getChapterKnowledgeContent(
        courseId,
        chapterId,
        token,
      );
      setKnowledgeContent(knowledgeData);
    } catch (error) {
      console.error("Failed to fetch knowledge content:", error);
      // If knowledge fails, still allow to proceed with quiz
      setKnowledgeContent(null);
    } finally {
      setKnowledgeLoading(false);
    }
  };

  // Start base quiz after viewing knowledge
  // targetQuestionId: 目标题目的 question_id，如果为 0 则从头开始或恢复进度
  const handleStartBaseQuiz = async (targetQuestionId: number = 0) => {
    const token = getStoredToken();
    if (!token || !selectedChapterId) return;

    setBaseQuestionLoading(true);
    setStep("base_quiz");

    try {
      // 并行获取题目和进度
      const [data, progressData] = await Promise.all([
        getChapterBaseQuestions(courseId, selectedChapterId, token),
        getMasteryChapterDetailProgress(
          courseId,
          selectedChapterId,
          token,
        ).catch(() => null),
      ]);
      setBaseQuestions(data.questions);

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
      if (startQuestion && completedMap.has(startQuestion.id)) {
        setSubmitted(true);
        setIsCorrect(completedMap.get(startQuestion.id) || false);
      } else {
        setSubmitted(false);
        setIsCorrect(false);
      }

      console.log(
        `[精进之路] 开始答题: 起始题目=${startIndex + 1}, 总题数=${data.questions.length}, 已恢复答案=${restoredAnswers.size}个, 已完成=${completedMap.size}个`,
      );
    } catch (error) {
      console.error("Failed to fetch base questions:", error);
      alert("加载测试题失败，请稍后重试");
      setStep("knowledge");
    } finally {
      setBaseQuestionLoading(false);
    }
  };

  // Handle base answer submission
  const handleSubmitBaseAnswer = async () => {
    const currentQuestion = baseQuestions[currentQuestionIndex];
    const answer = baseAnswers.get(currentQuestion.id);
    if (!answer) return;

    const questionType = getQuestionType(currentQuestion);
    let correct = false;

    if (questionType === "choice") {
      // Choice question: compare option letter
      correct =
        answer.toUpperCase() === currentQuestion.correct_answer?.toUpperCase();
    } else if (questionType === "fill_blank") {
      // Fill blank: compare answer content (trim whitespace, case-insensitive for simplicity)
      const userAnswer = answer.trim();
      const correctAnswer = currentQuestion.correct_answer?.trim() || "";
      // For fill blank, do case-insensitive comparison and allow multiple correct answers separated by |
      const correctOptions = correctAnswer
        .split("|")
        .map((s) => s.trim().toLowerCase());
      correct = correctOptions.includes(userAnswer.toLowerCase());
    } else if (questionType === "programming") {
      // Programming: for now, always mark as submitted (needs server evaluation)
      correct = false;
    } else {
      // Default: compare as choice
      correct =
        answer.toUpperCase() === currentQuestion.correct_answer?.toUpperCase();
    }

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
        await saveMasteryExerciseProgress(
          {
            course_id: courseId,
            chapter_id: selectedChapterId,
            question_id: currentQuestion.id,
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
        console.log("[精进之路] 进度保存成功");
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
            exercise_content: {
              text: currentQuestion.text,
              options: currentQuestion.options,
              type: questionType,
            },
            exercise_type: questionType,
            knowledge_points: currentQuestion.knowledge_points || [],
          });
          console.log("[精进之路] 错题收集成功");
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
      if (nextQuestion && completedQuestionsMap.has(nextQuestion.id)) {
        setSubmitted(true);
        setIsCorrect(completedQuestionsMap.get(nextQuestion.id) || false);
      } else {
        setSubmitted(false);
        setIsCorrect(false);
      }
    } else {
      // Submit all answers
      await handleSubmitAllBaseAnswers();
    }
  };

  // Submit all base answers and get analysis
  const handleSubmitAllBaseAnswers = async () => {
    const token = getStoredToken();
    if (!token || !selectedChapterId) return;

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
        { answers: answersArray },
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
          console.log("[精进之路] 章节进度更新成功");
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

  // Generate enhanced quiz based on weak points
  const handleStartEnhancedQuiz = async () => {
    const token = getStoredToken();
    if (!token || !selectedChapterId) return;

    setEnhancedLoading(true);

    try {
      const response = await generateEnhancedQuiz(
        courseId,
        {
          course_id: courseId,
          chapter_id: selectedChapterId,
          weak_points: baseResult?.weak_points || [],
          strong_points: baseResult?.strong_points || [],
          question_count: 3,
          question_types: ["choice"],
        },
        token,
      );

      if (response.success && response.questions.length > 0) {
        setEnhancedQuestions(response.questions);
        setEnhancedSessionId(response.session_id);
        setEnhancedAnswers(new Map());
        setCurrentQuestionIndex(0);
        setSubmitted(false);
        setStep("enhanced_quiz");
      } else {
        // No weak points, show success
        setFinalResult({
          success: true,
          session_id: "",
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
      }
    } catch (error) {
      console.error("Failed to generate enhanced quiz:", error);
      alert("生成强化测试失败，请稍后重试");
    } finally {
      setEnhancedLoading(false);
    }
  };

  // Submit enhanced answer
  const handleSubmitEnhancedAnswer = async () => {
    const currentQuestion = enhancedQuestions[currentQuestionIndex];
    const answer = enhancedAnswers.get(currentQuestion.id);
    if (!answer) return;

    // Check if correct
    const correct =
      answer.toUpperCase() === currentQuestion.correct_answer?.toUpperCase();

    setSubmitted(true);

    // Collect wrong question if incorrect
    if (!correct) {
      const token = getStoredToken();
      if (token) {
        try {
          const exerciseKey = `enhanced-${courseId}-${enhancedSessionId}-${currentQuestion.id}`;
          await collectWrongQuestion(token, {
            exercise_key: exerciseKey,
            user_answer: answer,
            course_id: courseId,
            exercise_content: {
              text: currentQuestion.text,
              options: currentQuestion.options,
              type: "choice",
            },
            exercise_type: "choice",
            knowledge_points: currentQuestion.knowledge_points || [],
          });
          console.log("[强化测试] 错题收集成功");
        } catch (error) {
          console.error("[强化测试] 错题收集失败:", error);
        }
      }
    }
  };

  // Move to next enhanced question or submit all
  const handleNextEnhancedQuestion = async () => {
    if (currentQuestionIndex < enhancedQuestions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setSubmitted(false);
    } else {
      // Submit all enhanced answers
      await handleSubmitAllEnhancedAnswers();
    }
  };

  // Submit all enhanced answers
  const handleSubmitAllEnhancedAnswers = async () => {
    const token = getStoredToken();
    if (!token) return;

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
          session_id: enhancedSessionId,
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
  };

  useEffect(() => {
    return () => {
      void endTrackedSession();
    };
  }, [endTrackedSession]);

  // Back to chapter selection
  const handleBackToChapters = async () => {
    await endTrackedSession();
    setStep("select_chapter");
    setSelectedChapterId(null);
    setBaseQuestions([]);
    setBaseAnswers(new Map());
    setCompletedQuestionsMap(new Map());
    setBaseResult(null);
    setEnhancedQuestions([]);
    setEnhancedAnswers(new Map());
    setFinalResult(null);
    setKnowledgeContent(null);

    // Clear URL params to prevent re-triggering jump from wrong question book
    const hasJumpParams =
      searchParams.get("chapter") ||
      searchParams.get("exercise") ||
      searchParams.get("skip");
    if (hasJumpParams) {
      router.replace(`/mastery/${courseId}`, { scroll: false });
    }

    fetchOverview();
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  // Result state
  if (step === "result" && finalResult) {
    const passed = finalResult.passed;
    const accuracy = Math.round(finalResult.accuracy * 100);

    return (
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-amber-500" />
              <span className="font-semibold">测试结果</span>
            </div>
            <div className="w-20"></div>
          </div>
        </header>

        <main className="pt-24 pb-12 px-4">
          <div className="max-w-md mx-auto">
            <div
              className={`rounded-2xl border p-8 text-center mb-6 ${
                passed
                  ? "bg-emerald-500/10 border-emerald-500/30"
                  : "bg-orange-500/10 border-orange-500/30"
              }`}
            >
              {passed ? (
                <CheckCircle className="w-20 h-20 text-emerald-500 mx-auto mb-4" />
              ) : (
                <XCircle className="w-20 h-20 text-orange-400 mx-auto mb-4" />
              )}

              <h2 className="text-2xl font-bold text-foreground mb-2">
                {passed ? "恭喜通过！" : "继续努力"}
              </h2>

              <p className="text-muted-foreground mb-6">
                {finalResult.total_questions > 0 && (
                  <>
                    答对 {finalResult.correct_answers}/
                    {finalResult.total_questions} 题 ({accuracy}%)
                  </>
                )}
              </p>

              <div className="bg-card rounded-xl p-4 mb-6 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">获得经验值</span>
                  <span className="font-medium text-blue-500">
                    +{finalResult.xp_earned}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">掌握点数</span>
                  <span className="font-medium text-amber-500">
                    +{finalResult.mastery_points_earned}
                  </span>
                </div>
              </div>

              {finalResult.recommendations.length > 0 && (
                <div className="bg-muted/50 rounded-xl p-4 text-left text-sm">
                  <p className="font-medium text-foreground mb-2">学习建议</p>
                  <ul className="text-muted-foreground space-y-1">
                    {finalResult.recommendations.map((rec, i) => (
                      <li key={i}>• {rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <button
              onClick={handleBackToChapters}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 transition-all"
            >
              返回章节列表
            </button>
          </div>
        </main>
      </div>
    );
  }

  // Knowledge state - show knowledge points before quiz
  if (step === "knowledge") {
    return (
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <button
              onClick={handleBackToChapters}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">返回</span>
            </button>
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-500" />
              <span className="font-semibold">{selectedChapterTitle}</span>
            </div>
            <div className="w-20"></div>
          </div>
        </header>

        <main className="pt-20 pb-24 px-4">
          <div className="max-w-3xl mx-auto">
            {knowledgeLoading ? (
              <div className="text-center py-16">
                <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-muted-foreground">加载知识点...</p>
              </div>
            ) : knowledgeContent ? (
              <div className="space-y-6">
                {/* Header */}
                <div className="text-center mb-8">
                  <h1 className="text-2xl font-bold text-foreground mb-2">
                    {knowledgeContent.chapter_title}
                  </h1>
                  <p className="text-muted-foreground">知识点讲解</p>
                  <div className="flex items-center justify-center gap-4 mt-4 text-sm text-muted-foreground">
                    <span>{knowledgeContent.total_points} 个知识点</span>
                    <span>•</span>
                    <span>预计 {knowledgeContent.estimated_time} 分钟</span>
                  </div>
                </div>

                {/* Knowledge Points */}
                <div className="space-y-4">
                  {knowledgeContent.knowledge_points.map((point, index) => (
                    <div
                      key={point.id}
                      className="bg-card rounded-2xl border border-border p-6"
                    >
                      <div className="flex items-start gap-4">
                        <span className="flex-shrink-0 w-8 h-8 bg-amber-500/20 text-amber-600 rounded-full flex items-center justify-center font-medium">
                          {index + 1}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-foreground">
                              {point.title}
                            </h3>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${
                                point.difficulty === 1
                                  ? "bg-green-500/20 text-green-400"
                                  : point.difficulty === 2
                                    ? "bg-blue-500/20 text-blue-400"
                                    : point.difficulty === 3
                                      ? "bg-yellow-500/20 text-yellow-400"
                                      : point.difficulty === 4
                                        ? "bg-orange-500/20 text-orange-400"
                                        : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {point.difficulty === 1
                                ? "入门"
                                : point.difficulty === 2
                                  ? "基础"
                                  : point.difficulty === 3
                                    ? "中等"
                                    : point.difficulty === 4
                                      ? "较难"
                                      : "困难"}
                            </span>
                          </div>
                          <p className="text-muted-foreground leading-relaxed mb-4">
                            {point.content}
                          </p>

                          {/* Code Examples */}
                          {point.examples && point.examples.length > 0 && (
                            <div className="space-y-2">
                              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                示例代码
                              </p>
                              {point.examples.map((example, i) => (
                                <div
                                  key={i}
                                  className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm overflow-x-auto"
                                >
                                  <pre>{example}</pre>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Related Points */}
                          {point.related_points &&
                            point.related_points.length > 0 && (
                              <div className="mt-4 text-sm text-muted-foreground">
                                <span className="font-medium">
                                  相关知识点：
                                </span>
                                {point.related_points.join("、")}
                              </div>
                            )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-16 bg-card rounded-2xl border border-border">
                <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
                <p className="text-muted-foreground mb-4">无法加载知识点内容</p>
                <p className="text-sm text-muted-foreground">
                  您可以继续进行测试
                </p>
              </div>
            )}
          </div>
        </main>

        {/* Bottom action bar */}
        <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
          <div className="max-w-3xl mx-auto px-4 py-4">
            <button
              onClick={() => handleStartBaseQuiz()}
              disabled={baseQuestionLoading}
              className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {baseQuestionLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  加载测试题...
                </>
              ) : (
                <>
                  <BookOpen className="w-5 h-5" />
                  开始基础测试
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Analysis state - show weak points and offer enhanced quiz
  if (step === "analysis" && baseResult) {
    const accuracy = Math.round(baseResult.accuracy * 100);

    return (
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <button
              onClick={handleBackToChapters}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">退出</span>
            </button>
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-amber-500" />
              <span className="font-semibold">学习分析</span>
            </div>
            <div className="w-20"></div>
          </div>
        </header>

        <main className="pt-24 pb-12 px-4">
          <div className="max-w-md mx-auto">
            {/* Summary */}
            <div className="bg-card rounded-2xl border border-border p-6 mb-6">
              <div className="text-center mb-6">
                <p className="text-4xl font-bold text-foreground mb-2">
                  {accuracy}%
                </p>
                <p className="text-muted-foreground">基础测试正确率</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-emerald-500/10 rounded-xl p-3">
                  <p className="text-2xl font-bold text-emerald-500">
                    {baseResult.correct_answers}
                  </p>
                  <p className="text-xs text-muted-foreground">正确</p>
                </div>
                <div className="bg-red-500/10 rounded-xl p-3">
                  <p className="text-2xl font-bold text-red-400">
                    {baseResult.total_questions - baseResult.correct_answers}
                  </p>
                  <p className="text-xs text-muted-foreground">错误</p>
                </div>
              </div>
            </div>

            {/* Weak points */}
            {baseResult.weak_points.length > 0 && (
              <div className="bg-orange-500/10 rounded-2xl border border-orange-500/20 p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-5 h-5 text-orange-500" />
                  <span className="font-medium text-foreground">
                    需要强化的知识点
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {baseResult.weak_points.map((point, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Strong points */}
            {baseResult.strong_points.length > 0 && (
              <div className="bg-emerald-500/10 rounded-2xl border border-emerald-500/20 p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                  <span className="font-medium text-foreground">
                    已掌握的知识点
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {baseResult.strong_points.map((point, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-sm"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            {baseResult.weak_points.length > 0 ? (
              <button
                onClick={handleStartEnhancedQuiz}
                disabled={enhancedLoading}
                className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              >
                {enhancedLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    生成强化测试...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    开始强化测试
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleBackToChapters}
                className="w-full py-4 bg-gradient-to-r from-emerald-500 to-emerald-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-emerald-500/25 transition-all"
              >
                完成！返回章节列表
              </button>
            )}

            <button
              onClick={handleBackToChapters}
              className="w-full mt-3 py-3 bg-card border border-border rounded-xl font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              跳过强化，返回章节
            </button>
          </div>
        </main>
      </div>
    );
  }

  // Enhanced quiz state
  if (step === "enhanced_quiz" && enhancedQuestions.length > 0) {
    const currentQuestion = enhancedQuestions[currentQuestionIndex];
    const isLastQuestion =
      currentQuestionIndex === enhancedQuestions.length - 1;

    return (
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <button
              onClick={handleBackToChapters}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">退出</span>
            </button>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              <span className="font-semibold">强化测试</span>
            </div>
            <div className="flex items-center gap-1">
              {enhancedQuestions.map((_, i) => (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    i < currentQuestionIndex
                      ? "bg-emerald-400"
                      : i === currentQuestionIndex
                        ? "bg-primary"
                        : "bg-muted"
                  }`}
                />
              ))}
            </div>
          </div>
        </header>

        <main className="pt-20 pb-24 px-4">
          <div className="max-w-2xl mx-auto">
            {/* Question header */}
            <div className="flex items-center gap-3 mb-6">
              <span className="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium">
                {currentQuestionIndex + 1} / {enhancedQuestions.length}
              </span>
              <span
                className={`px-3 py-1 rounded-lg text-xs font-medium border ${DIFFICULTY_COLORS[currentQuestion.difficulty]}`}
              >
                难度 {currentQuestion.difficulty}
              </span>
              <span className="text-xs text-muted-foreground">强化题</span>
            </div>

            {/* Question */}
            <div className="bg-card rounded-2xl border border-border p-6 mb-6">
              <h2 className="text-xl font-bold text-foreground mb-4">
                {currentQuestion.text}
              </h2>

              {currentQuestion.knowledge_points.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {currentQuestion.knowledge_points.map((kp, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-orange-500/10 text-orange-400 text-xs rounded-full"
                    >
                      {kp}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Options */}
            {currentQuestion.options && (
              <div className="space-y-3">
                {currentQuestion.options.map((opt, i) => {
                  const optLabel = String.fromCharCode(65 + i);
                  return (
                    <button
                      key={optLabel}
                      onClick={() =>
                        !submitted &&
                        setEnhancedAnswers((prev) =>
                          new Map(prev).set(currentQuestion.id, optLabel),
                        )
                      }
                      disabled={submitted}
                      className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                        enhancedAnswers.get(currentQuestion.id) === optLabel
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-muted hover:bg-muted/30"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                            enhancedAnswers.get(currentQuestion.id) === optLabel
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {optLabel}
                        </span>
                        <span className="text-foreground">{opt}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </main>

        {/* Bottom action bar */}
        <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
          <div className="max-w-2xl mx-auto px-4 py-4">
            <button
              onClick={
                submitted
                  ? handleNextEnhancedQuestion
                  : handleSubmitEnhancedAnswer
              }
              disabled={
                !enhancedAnswers.get(currentQuestion.id) || enhancedLoading
              }
              className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {enhancedLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  提交中...
                </span>
              ) : submitted ? (
                isLastQuestion ? (
                  "完成测试"
                ) : (
                  "下一题"
                )
              ) : (
                "提交答案"
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Base quiz state
  if (step === "base_quiz" && baseQuestions.length > 0) {
    const currentQuestion = baseQuestions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === baseQuestions.length - 1;

    return (
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <button
              onClick={handleBackToChapters}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">退出</span>
            </button>
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-500" />
              <span className="font-semibold">{selectedChapterTitle}</span>
            </div>
            <div className="flex items-center gap-1">
              {baseQuestions.map((q, i) => {
                const isCompleted = completedQuestionsMap.has(q.id);
                const wasCorrect = completedQuestionsMap.get(q.id) || false;
                return (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      isCompleted
                        ? wasCorrect
                          ? "bg-emerald-400"
                          : "bg-red-400"
                        : i === currentQuestionIndex
                          ? "bg-primary"
                          : "bg-muted"
                    }`}
                  />
                );
              })}
            </div>
          </div>
        </header>

        <main className="pt-20 pb-24 px-4">
          <div className="max-w-2xl mx-auto">
            {/* Question header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium">
                  {currentQuestionIndex + 1} / {baseQuestions.length}
                </span>
                <span
                  className={`px-3 py-1 rounded-lg text-xs font-medium border ${DIFFICULTY_COLORS[currentQuestion.difficulty]}`}
                >
                  {currentQuestion.difficulty === 1 ? "入门" : "基础"}
                </span>
              </div>
              {/* 收藏按钮 */}
              <FavoriteButton
                exerciseKey={`mastery-${courseId}-${selectedChapterId}-${currentQuestion.id}`}
                courseId={courseId}
                exerciseId={currentQuestion.id}
                chapterId={selectedChapterId || undefined}
                exerciseContent={{
                  text: currentQuestion.text,
                  options: currentQuestion.options,
                }}
                exerciseType={getQuestionType(currentQuestion)}
                exerciseDifficulty={currentQuestion.difficulty}
                knowledgePoints={currentQuestion.knowledge_points}
                size="sm"
              />
            </div>

            {/* Question type indicator */}
            <div className="mb-4">
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-xs font-medium">
                {getQuestionType(currentQuestion) === "choice"
                  ? "选择题"
                  : getQuestionType(currentQuestion) === "fill_blank"
                    ? "填空题"
                    : getQuestionType(currentQuestion) === "programming"
                      ? "编程题"
                      : "选择题"}
              </span>
            </div>

            {/* Question */}
            <div className="bg-card rounded-2xl border border-border p-6 mb-6">
              <h2 className="text-xl font-bold text-foreground mb-4">
                {currentQuestion.text}
              </h2>

              {currentQuestion.knowledge_points.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {currentQuestion.knowledge_points.map((kp, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
                    >
                      {kp}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Choice Options */}
            {getQuestionType(currentQuestion) === "choice" &&
              currentQuestion.options &&
              currentQuestion.options.length > 0 && (
                <div className="space-y-3">
                  {currentQuestion.options.map((opt, i) => {
                    const optLabel = String.fromCharCode(65 + i);
                    const isSelected =
                      baseAnswers.get(currentQuestion.id) === optLabel;
                    const isCorrectOption =
                      currentQuestion.correct_answer?.toUpperCase() ===
                      optLabel;

                    return (
                      <button
                        key={optLabel}
                        onClick={() =>
                          !submitted &&
                          setBaseAnswers((prev) =>
                            new Map(prev).set(currentQuestion.id, optLabel),
                          )
                        }
                        disabled={submitted}
                        className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                          submitted
                            ? isSelected
                              ? isCorrect
                                ? "border-emerald-500 bg-emerald-500/10"
                                : "border-red-500 bg-red-500/10"
                              : isCorrectOption
                                ? "border-emerald-500 bg-emerald-500/5"
                                : "border-border opacity-50"
                            : isSelected
                              ? "border-primary bg-primary/10"
                              : "border-border hover:border-muted hover:bg-muted/30"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                              submitted
                                ? isSelected && isCorrect
                                  ? "bg-emerald-500 text-white"
                                  : isSelected && !isCorrect
                                    ? "bg-red-500 text-white"
                                    : isCorrectOption
                                      ? "bg-emerald-500 text-white"
                                      : "bg-muted text-muted-foreground"
                                : isSelected
                                  ? "bg-primary text-primary-foreground"
                                  : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {submitted && isCorrectOption ? (
                              <CheckCircle className="w-4 h-4" />
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
              <div className="space-y-4">
                <div className="bg-card rounded-xl border border-border p-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    请输入答案：
                  </label>
                  <input
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
                    className={`w-full p-4 rounded-xl border-2 bg-background text-foreground transition-all ${
                      submitted
                        ? isCorrect
                          ? "border-emerald-500 bg-emerald-500/10"
                          : "border-red-500 bg-red-500/10"
                        : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                    } disabled:opacity-70`}
                  />
                </div>

                {submitted && (
                  <div
                    className={`p-4 rounded-xl ${isCorrect ? "bg-emerald-500/10" : "bg-red-500/10"}`}
                  >
                    <p className="text-sm font-medium text-foreground mb-1">
                      {isCorrect ? "✅ 正确！" : "❌ 错误"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      正确答案：
                      <span className="font-medium text-emerald-500">
                        {currentQuestion.correct_answer}
                      </span>
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Programming Question */}
            {getQuestionType(currentQuestion) === "programming" && (
              <div className="space-y-4">
                <div className="bg-card rounded-xl border border-border p-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    请编写代码：
                  </label>
                  {currentQuestion.code_template && (
                    <div className="mb-3 p-3 bg-muted/50 rounded-lg font-mono text-sm text-muted-foreground">
                      <pre>{currentQuestion.code_template}</pre>
                    </div>
                  )}
                  <textarea
                    value={baseAnswers.get(currentQuestion.id) || ""}
                    onChange={(e) =>
                      !submitted &&
                      setBaseAnswers((prev) =>
                        new Map(prev).set(currentQuestion.id, e.target.value),
                      )
                    }
                    disabled={submitted}
                    placeholder="在此编写您的代码..."
                    rows={8}
                    className={`w-full p-4 rounded-xl border-2 bg-background text-foreground font-mono text-sm transition-all ${
                      submitted
                        ? "border-border bg-muted/50"
                        : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                    } disabled:opacity-70`}
                  />
                </div>

                {submitted && (
                  <div className="p-4 rounded-xl bg-blue-500/10">
                    <p className="text-sm text-muted-foreground">
                      代码已提交，请等待教师批改或查看参考答案。
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Explanation after submission */}
            {submitted && currentQuestion.explanation && (
              <div
                className={`mt-6 p-4 rounded-xl ${isCorrect ? "bg-emerald-500/10" : "bg-blue-500/10"}`}
              >
                <p className="text-sm font-medium text-foreground mb-2">解析</p>
                <p className="text-sm text-muted-foreground">
                  {currentQuestion.explanation}
                </p>
              </div>
            )}
          </div>
        </main>

        {/* Bottom action bar */}
        <div
          className={`fixed bottom-0 left-0 right-0 border-t transition-colors ${
            submitted
              ? isCorrect
                ? "bg-emerald-500/10 border-emerald-500/30"
                : "bg-red-500/10 border-red-500/20"
              : "bg-card border-border"
          }`}
        >
          <div className="max-w-2xl mx-auto px-4 py-4">
            {submitted ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {isCorrect ? (
                    <>
                      <CheckCircle className="w-6 h-6 text-emerald-500" />
                      <span className="font-medium text-emerald-500">
                        正确！
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-6 h-6 text-red-400" />
                      <span className="font-medium text-red-400">错误</span>
                    </>
                  )}
                </div>
                <button
                  onClick={handleNextQuestion}
                  disabled={baseQuestionLoading}
                  className="px-8 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                >
                  {baseQuestionLoading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <>
                      {isLastQuestion ? "查看结果" : "下一题"}
                      <ChevronRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            ) : (
              <button
                onClick={handleSubmitBaseAnswer}
                disabled={!baseAnswers.get(currentQuestion.id)}
                className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-amber-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                提交答案
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Default: Chapter selection
  return (
    <div className="min-h-screen bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">返回</span>
          </Link>
          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            <span className="font-semibold">精进之路</span>
          </div>
          <div className="w-20"></div>
        </div>
      </header>

      <main className="pt-20 pb-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Progress Overview */}
          {overview && (
            <div className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-2xl border border-amber-500/20 p-6 mb-8">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-foreground">
                    学习进度
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    已完成 {overview.mastered_chapters}/
                    {overview.total_chapters} 章节
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-amber-500">
                    {overview.total_mastery_score?.toFixed(0) ?? 0}
                  </p>
                  <p className="text-xs text-muted-foreground">掌握分数</p>
                </div>
              </div>
              <div className="h-2 bg-amber-500/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all"
                  style={{
                    width: `${overview.total_chapters > 0 ? (overview.mastered_chapters / overview.total_chapters) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          )}

          {/* Chapter List */}
          <h3 className="text-lg font-semibold text-foreground mb-4">
            选择章节开始学习
          </h3>

          {overview?.chapters && overview.chapters.length > 0 ? (
            <div className="space-y-3">
              {overview.chapters.map((chapter) => {
                const masteryPercent = chapter.mastery_score ?? 0;
                const masteryLevel = chapter.mastery_level as MasteryLevel;
                const isUnlocked =
                  chapter.order_index === 1 ||
                  overview.chapters.find(
                    (c) => c.order_index === chapter.order_index - 1,
                  )?.can_advance ||
                  (chapter.mastery_score ?? 0) > 0;

                return (
                  <button
                    key={chapter.chapter_id}
                    onClick={() =>
                      isUnlocked &&
                      handleSelectChapter(chapter.chapter_id, chapter.title)
                    }
                    disabled={!isUnlocked}
                    className={`w-full p-4 rounded-xl border text-left transition-all ${
                      isUnlocked
                        ? "border-border hover:border-amber-500/50 hover:bg-amber-500/5"
                        : "border-border/50 bg-muted/30 cursor-not-allowed opacity-60"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center font-medium ${
                            isUnlocked
                              ? "bg-amber-500/20 text-amber-600"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {chapter.order_index}
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {chapter.title}
                          </p>
                          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                            <span
                              className={
                                MASTERY_LEVEL_COLORS[masteryLevel] ||
                                "text-muted-foreground"
                              }
                            >
                              {masteryLevel}
                            </span>
                            <span>•</span>
                            <span>掌握度 {masteryPercent.toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>
                      <ChevronRight
                        className={`w-5 h-5 ${isUnlocked ? "text-muted-foreground" : "text-muted-foreground/50"}`}
                      />
                    </div>

                    {/* Progress bar */}
                    <div className="mt-3 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full transition-all"
                        style={{ width: `${masteryPercent}%` }}
                      />
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-16 bg-card rounded-2xl border border-border">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground">暂无章节内容</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
