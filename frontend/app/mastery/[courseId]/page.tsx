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
import { KnowledgeOrb } from "@/components/ui/knowledge-orb";
import { CourseMasteryOverview } from "@/components/mastery/MasteryComponents";

import {
  getMasteryOverview,
  getSectionBaseQuestions,
  submitBaseAnswers,
  generateEnhancedQuiz,
  submitEnhancedQuiz,
  getStoredToken,
  logout,
  MASTERY_LEVEL_COLORS,
  startLearningSession,
  endLearningSession,
  getCourseMastery,
  type CourseMasteryResponse,
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
} from "@/types/api";

type MasteryStep =
  | "select_chapter"
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

  // BKT Course Mastery state
  const [courseMastery, setCourseMastery] = useState<CourseMasteryResponse | null>(null);

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

  // Track answers modified in current session (not restored from history)
  // This ensures we only submit new answers, not all historical answers
  const [currentSessionAnswers, setCurrentSessionAnswers] = useState<
    Set<number>
  >(new Set());

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

  // Track learning session state
  const sessionStartedAtRef = useRef<number | null>(null);
  const activeSessionChapterIdRef = useRef<number | null>(null);
  const isEndingSessionRef = useRef(false);
  const sessionInitializedRef = useRef(false); // 防止 StrictMode 重复初始化
  const sessionEndedRef = useRef(false); // 防止 StrictMode 重复结束
  const currentSectionIdRef = useRef<number | null>(null); // 保存当前 sectionId，避免 state 丢失

  const fetchOverview = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      logout();
      router.push("/login");
      return;
    }

    try {
      // 并行获取 overview 和 course mastery
      const [data, masteryData] = await Promise.all([
        getMasteryOverview(courseId, token),
        getCourseMastery(courseId, token).catch(() => null),
      ]);
      setOverview(data);
      setCourseMastery(masteryData);
    } catch (error) {
      console.error("Failed to fetch mastery overview:", error);
    } finally {
      setLoading(false);
    }
  }, [courseId, router]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  // Handle query params for jump from wrong question book or section learning
  useEffect(() => {
    const chapterParam = searchParams.get("chapter");
    const sectionParam = searchParams.get("section");
    const exerciseParam = searchParams.get("exercise");

    console.log("[精进之路-DEBUG] useEffect 触发, URL参数:", { chapterParam, sectionParam, exerciseParam, overviewLoaded: !!overview?.chapters });

    // 如果没有必要的参数，不处理
    if (!chapterParam) {
      console.log("[精进之路-DEBUG] 没有 chapter 参数，跳过");
      return;
    }

    if (!overview?.chapters) {
      console.log("[精进之路-DEBUG] overview 未加载，跳过");
      return;
    }

    const chapterId = parseInt(chapterParam);
    const chapter = overview.chapters.find((c) => c.chapter_id === chapterId);

    console.log("[精进之路-DEBUG] 找到章节:", { chapterId, found: !!chapter, chapterTitle: chapter?.title });

    if (!chapter) {
      console.log("[精进之路-DEBUG] 未找到章节，跳过");
      return;
    }

    // 保存 section_id（如果有）
    const sectionId = sectionParam ? parseInt(sectionParam) : null;
    console.log("[精进之路-DEBUG] 解析 sectionId:", sectionId);

    // 跳转到具体题目
    // exerciseParam 是 question_id，需要在获取题目列表后找到对应索引
    const targetQuestionId = exerciseParam ? parseInt(exerciseParam) : 0;

    // Directly start quiz at the target question
    console.log("[精进之路-DEBUG] 调用 startQuizAtQuestion:", { chapterId, targetQuestionId, sectionId });
    startQuizAtQuestion(chapterId, targetQuestionId, sectionId || undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, overview]);

  const startTrackedSession = useCallback(async (chapterId: number) => {
    const token = getStoredToken();
    if (!token) return;

    console.log("[精进之路-学习时长] startTrackedSession 调用, chapterId =", chapterId);
    console.log("[精进之路-学习时长] activeSessionChapterIdRef =", activeSessionChapterIdRef.current);
    console.log("[精进之路-学习时长] sessionStartedAtRef =", sessionStartedAtRef.current);

    // 检查是否有从其他页面转移过来的会话
    const continueSession = searchParams.get("continueSession") === "1";
    if (continueSession) {
      try {
        const savedSession = localStorage.getItem('masterySession');
        if (savedSession) {
          const sessionData = JSON.parse(savedSession);
          console.log("[精进之路-学习时长] 检测到继续会话，从 localStorage 恢复:", sessionData);
          activeSessionChapterIdRef.current = sessionData.chapterId;
          sessionStartedAtRef.current = sessionData.startedAt;
          sessionInitializedRef.current = true;
          sessionEndedRef.current = false;
          // 清除 localStorage 中的会话数据
          localStorage.removeItem('masterySession');
          console.log("[精进之路-学习时长] 会话已恢复，开始时间:", new Date(sessionData.startedAt).toLocaleString());
          return;
        }
      } catch (e) {
        console.error("[精进之路-学习时长] 解析会话数据失败:", e);
      }
    }

    if (
      activeSessionChapterIdRef.current === chapterId &&
      sessionStartedAtRef.current
    ) {
      console.log("[精进之路-学习时长] 同一章节已有会话，跳过");
      return;
    }

    if (
      activeSessionChapterIdRef.current !== null &&
      sessionStartedAtRef.current
    ) {
      console.log("[精进之路-学习时长] 切换章节，先结束上一段会话");
      const prevChapterId = activeSessionChapterIdRef.current ?? undefined;
      const durationSeconds = Math.max(
        1,
        Math.floor((Date.now() - sessionStartedAtRef.current) / 1000),
      );
      activeSessionChapterIdRef.current = null;
      sessionStartedAtRef.current = null;
      sessionInitializedRef.current = false;
      try {
        // Await here since we're about to start a new session — must finish first
        await endLearningSession(token, durationSeconds, prevChapterId);
      } catch (error) {
        console.error("[精进之路] 结束上一段学习会话失败:", error);
      }
    }

    try {
      console.log("[精进之路-学习时长] ========== 开始新会话 ==========");
      console.log("[精进之路-学习时长] 调用 startLearningSession, chapterId =", chapterId);
      await startLearningSession(token, chapterId, 0);
      const now = Date.now();
      activeSessionChapterIdRef.current = chapterId;
      sessionStartedAtRef.current = now;
      sessionInitializedRef.current = true;
      sessionEndedRef.current = false; // 重置结束标记
      console.log("[精进之路-学习时长] 会话已启动，开始时间:", new Date(now).toLocaleString());
    } catch (error) {
      console.error("[精进之路] 开始学习会话失败:", error);
    }
  }, [searchParams]);

  const endTrackedSession = useCallback(async () => {
    console.log("[精进之路-学习时长] endTrackedSession 被调用");
    console.log("[精进之路-学习时长] sessionEndedRef.current =", sessionEndedRef.current);

    if (sessionEndedRef.current) {
      console.log("[精进之路-学习时长] 会话已结束，跳过");
      return;
    }

    const token = getStoredToken();
    const startedAt = sessionStartedAtRef.current;

    console.log("[精进之路-学习时长] token 存在:", !!token);
    console.log("[精进之路-学习时长] startedAt =", startedAt);
    console.log("[精进之路-学习时长] sessionInitializedRef =", sessionInitializedRef.current);

    if (
      !token ||
      !startedAt ||
      !sessionInitializedRef.current
    ) {
      console.log("[精进之路-学习时长] 条件不满足，跳过");
      return;
    }

    const durationSeconds = Math.max(
      1,
      Math.floor((Date.now() - startedAt) / 1000),
    );
    const durationMinutes = (durationSeconds / 60).toFixed(1);
    const chapterId = activeSessionChapterIdRef.current; // 先保存 chapterId

    console.log("[精进之路-学习时长] ========== 会话结束 ==========");
    console.log("[精进之路-学习时长] 开始时间:", new Date(startedAt).toLocaleString());
    console.log("[精进之路-学习时长] 结束时间:", new Date().toLocaleString());
    console.log("[精进之路-学习时长] 学习时长:", durationSeconds, "秒 (约", durationMinutes, "分钟)");
    console.log("[精进之路-学习时长] chapterId:", chapterId);

    sessionEndedRef.current = true;
    sessionInitializedRef.current = false;
    activeSessionChapterIdRef.current = null;
    sessionStartedAtRef.current = null;

    // Use keepalive so the request survives page navigation / component unmount
    console.log("[精进之路-学习时长] 调用 endLearningSessionKeepalive...");
    endLearningSessionKeepalive(token, durationSeconds, chapterId ?? undefined);
  }, []);

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
      console.log(`[精进之路-DEBUG] 请求 sectionId=${sectionId} 的题目`);
      const data = await getSectionBaseQuestions(sectionId, token);
      console.log(`[精进之路-DEBUG] 收到题目数据: section_id=${data.section_id}, section_title=${data.section_title}, 题目数量=${data.questions.length}`);
      if (data.questions.length > 0) {
        console.log(`[精进之路-DEBUG] 第一题: id=${data.questions[0].id}, text=${data.questions[0].text?.substring(0, 50)}...`);
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
        const weakPoints: string[] = [];
        const strongPoints: string[] = [];

        for (const q of data.questions) {
          const isCorrect = completedMap.get(q.id);
          if (isCorrect) {
            correctCount++;
            // 收集知识点作为强项
            for (const kp of q.knowledge_points || []) {
              if (!strongPoints.includes(kp)) {
                strongPoints.push(kp);
              }
            }
          } else {
            // 错题的知识点作为薄弱点
            for (const kp of q.knowledge_points || []) {
              if (!weakPoints.includes(kp)) {
                weakPoints.push(kp);
              }
            }
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
        });
        setStep("analysis");
        console.log(
          `[精进之路] 所有基础题已完成，直接进入分析界面: 正确=${correctCount}/${data.questions.length}`,
        );
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

  // Handle chapter selection - navigate to section selection page
  const handleSelectChapter = async (
    chapterId: number,
    chapterTitle: string,
  ) => {
    const token = getStoredToken();
    if (!token) return;

    // Store chapter info for section page
    try {
      localStorage.setItem('current_chapter_info', JSON.stringify({
        id: chapterId,
        title: chapterTitle,
        course_id: courseId,
        course_name: overview?.chapters[0]?.title || ''
      }));
    } catch (e) {
      console.warn('Failed to save chapter info to localStorage:', e);
    }

    // Navigate to section selection page
    router.push(`/mastery/${courseId}/chapter/${chapterId}`);
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
        const weakPoints: string[] = [];
        const strongPoints: string[] = [];

        for (const q of data.questions) {
          const isCorrect = completedMap.get(q.id);
          if (isCorrect) {
            correctCount++;
            // 收集知识点作为强项
            for (const kp of q.knowledge_points || []) {
              if (!strongPoints.includes(kp)) {
                strongPoints.push(kp);
              }
            }
          } else {
            // 错题的知识点作为薄弱点
            for (const kp of q.knowledge_points || []) {
              if (!weakPoints.includes(kp)) {
                weakPoints.push(kp);
              }
            }
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
        });
        setStep("analysis");
        console.log(
          `[精进之路] 所有基础题已完成，直接进入分析界面: 正确=${correctCount}/${data.questions.length}`,
        );
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
      if (startQuestion && completedMap.has(startQuestion.id)) {
        setSubmitted(true);
        setIsCorrect(completedMap.get(startQuestion.id) || false);
      } else {
        setSubmitted(false);
        setIsCorrect(false);
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
        const sectionIdToSave = selectedSectionId ?? currentSectionIdRef.current ?? undefined;
        await saveMasteryExerciseProgress(
          {
            course_id: courseId,
            chapter_id: selectedChapterId,
            section_id: sectionIdToSave,
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
        console.log("[精进之路] 进度保存成功, sectionId:", sectionIdToSave);
      } catch (error) {
        console.error("[精进之路] 进度保存失败:", error);
      }
    }

    // Collect wrong question if incorrect
    if (!correct) {
      if (token && selectedChapterId && selectedSectionId) {
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
    if (!token || !selectedChapterId || !selectedSectionId) {
      console.error("[精进之路] handleStartEnhancedQuiz: 缺少必要参数", { selectedChapterId, selectedSectionId });
      return;
    }

    currentSectionIdRef.current = selectedSectionId; // 保存到 ref，避免 state 丢失
    setEnhancedLoading(true);

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

    setIsCorrect(correct);
    setSubmitted(true);

    // 更新完成状态映射（强化题也需要记录）
    setCompletedQuestionsMap((prev) => {
      const newMap = new Map(prev);
      // currentQuestion.id 是字符串（数据库ID），转为数字
      const questionId = parseInt(currentQuestion.id, 10);
      if (!isNaN(questionId)) {
        newMap.set(questionId, correct);
      }
      return newMap;
    });

    // Save progress to backend (跟基础题一样的逻辑)
    const token = getStoredToken();
    // 使用 ref 作为后备，避免 state 丢失导致 section_id 为空
    const sectionIdToSave = selectedSectionId ?? currentSectionIdRef.current ?? undefined;
    if (token && selectedChapterId && sectionIdToSave) {
      const questionId = parseInt(currentQuestion.id, 10);
      // 统一使用 mastery- 前缀，方便与收藏去重匹配
      const exerciseKey = `mastery-${courseId}-${selectedChapterId}-${questionId}`;

      try {
        // 保存进度到 MasteryExerciseProgress 表
        console.log("[精进之路-强化题] 保存进度, sectionId:", sectionIdToSave);
        await saveMasteryExerciseProgress(
          {
            course_id: courseId,
            chapter_id: selectedChapterId,
            section_id: sectionIdToSave,
            question_id: questionId,
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
        console.log("[精进之路-强化题] 进度保存成功, question_id:", questionId);
      } catch (error) {
        console.error("[精进之路-强化题] 进度保存失败:", error);
      }

      // Collect wrong question if incorrect (跟基础题一样的逻辑)
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
          console.log("[精进之路-强化题] 错题收集成功, exercise_key:", exerciseKey);
        } catch (error) {
          console.error("[精进之路-强化题] 错题收集失败:", error);
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
          session_id: enhancedSessionId,
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
  };

  // 使用 isMountedRef 来区分 StrictMode 的假 unmount 和真正的 unmount
  const isMountedRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;
    console.log("[精进之路-学习时长] useEffect mount, isMountedRef =", isMountedRef.current);

    return () => {
      console.log("[精进之路-学习时长] useEffect cleanup");
      // 如果很快重新 mount，则 isMountedRef 会变回 true
      isMountedRef.current = false;

      // 延迟执行 endTrackedSession，给 StrictMode 重新 mount 的机会
      requestAnimationFrame(() => {
        console.log("[精进之路-学习时长] requestAnimationFrame callback, isMountedRef =", isMountedRef.current);
        if (!isMountedRef.current) {
          console.log("[精进之路-学习时长] 组件已真正卸载，结束会话");
          void endTrackedSession();
        } else {
          console.log("[精进之路-学习时长] 组件重新 mount，跳过结束会话");
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
    const fromSection = searchParams.get("fromSection");
    const chapterParam = searchParams.get("chapter");

    if (fromSection && chapterParam) {
      // Came from section learning page, return to the section learning page
      router.replace(`/mastery/${courseId}/chapter/${chapterParam}/section/${fromSection}`, { scroll: false });
    } else if (searchParams.get("chapter") || searchParams.get("exercise") || searchParams.get("skip")) {
      // Came from wrong question book or favorites, return to chapter selection
      router.replace(`/mastery/${courseId}`, { scroll: false });
    }

    fetchOverview();
  };

  // Loading state - only show for select_chapter step
  if (loading && step === "select_chapter") {
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
    const accuracy = Math.round(baseResult.accuracy * 100);

    return (
      <div className="min-h-screen bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <button
              onClick={handleViewQuestions}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">查看题目</span>
            </button>
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-amber-500" />
              <span className="font-semibold">学习分析</span>
            </div>
            <button
              onClick={handleBackToChapters}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              退出
            </button>
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

            <button
              onClick={handleBackToChapters}
              className="w-full mt-3 py-3 bg-card border border-border rounded-xl font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              暂时跳过，返回章节
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
                  const isSelected = enhancedAnswers.get(currentQuestion.id) === optLabel;
                  const isCorrectOption = currentQuestion.correct_answer?.toUpperCase() === optLabel;

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
            <div className="flex items-center gap-1.5">
              {(() => {
                // 显示5个题目，当前题始终在第3个位置（中间）
                const MAX_VISIBLE = 5;
                const CENTER_INDEX = 2;

                let start = currentQuestionIndex - CENTER_INDEX;
                let end = start + MAX_VISIBLE;

                // 边界处理：开头不够时
                if (start < 0) {
                  start = 0;
                  end = Math.min(baseQuestions.length, MAX_VISIBLE);
                }

                // 边界处理：结尾不够时
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
                    <button
                      key={q.id}
                      onClick={() => {
                        // 只能跳转到已完成的题目
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
                          ? "w-10 h-10 bg-primary text-primary-foreground scale-110 shadow-lg z-10"
                          : isCompleted
                            ? wasCorrect
                              ? "w-8 h-8 bg-emerald-100 text-emerald-700 border-2 border-emerald-400"
                              : "w-8 h-8 bg-red-100 text-red-700 border-2 border-red-400"
                            : globalIndex <= currentQuestionIndex
                              ? "w-8 h-8 bg-muted text-muted-foreground border border-border hover:border-primary"
                              : "w-8 h-8 bg-muted/50 text-muted-foreground/50 border border-border cursor-not-allowed"
                      }`}
                    >
                      {globalIndex + 1}
                    </button>
                  );
                });
              })()}
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
            <div
              className="bg-card rounded-2xl border border-border p-6 mb-6"
              data-question-context
              data-question-type={getQuestionType(currentQuestion)}
              data-question-id={currentQuestion.id}
              data-question-text={currentQuestion.text}
              data-question-options={JSON.stringify(currentQuestion.options || [])}
              data-question-answer-status={submitted ? (isCorrect ? "correct" : "wrong") : "unanswered"}
            >
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

        {/* AI Knowledge Assistant Orb - only available after submitting answer */}
        <KnowledgeOrb disabledForQuestion={!submitted} />
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
          {/* BKT Course Mastery Overview */}
          {courseMastery && (
            <div className="mb-8">
              {(() => {
                // 详细日志：每个章节的掌握度计算
                console.log("========== 课程掌握度计算 ==========");
                console.log(`API返回: courseMastery.mastery_score = ${courseMastery.mastery_score} (渲染到页面应该是 ${courseMastery.mastery_score.toFixed(0)}%)`);
                console.log(`章节数: ${courseMastery.chapters_count}, 已完成: ${courseMastery.completed_chapters}`);
                console.log("--- 各章节掌握度 ---");
                courseMastery.chapters.forEach((ch: any, idx: number) => {
                  if (idx < 2) {
                    console.log(`章节 ${idx + 1} (id=${ch.chapter_id}): mastery_score = ${ch.mastery_score} (${ch.mastery_score.toFixed(2)}%), 完成=${ch.is_completed}`);
                  }
                });

                // 按你的算法验证
                const ch1 = courseMastery.chapters[0];
                const ch2 = courseMastery.chapters[1];
                const kp1 = 64, kp2 = 10;
                const p1 = ch1.mastery_score / 100, p2 = ch2.mastery_score / 100;
                const totalKp = kp1 + kp2;
                const weighted = (kp1 * p1 + kp2 * p2) / totalKp;
                console.log("--- 验证课程整体（按你的算法）---");
                console.log(`第1章: ${kp1}个知识点 × ${ch1.mastery_score.toFixed(2)}% = ${(kp1 * p1).toFixed(2)}`);
                console.log(`第2章: ${kp2}个知识点 × ${ch2.mastery_score.toFixed(2)}% = ${(kp2 * p2).toFixed(2)}`);
                console.log(`总计: (${(kp1 * p1).toFixed(2)} + ${(kp2 * p2).toFixed(2)}) / ${totalKp} = ${(weighted * 100).toFixed(2)}%`);
                console.log(`API返回的 courseMastery.mastery_score = ${courseMastery.mastery_score.toFixed(2)}%`);
                console.log("=====================================");
                return null;
              })()}
              <CourseMasteryOverview
                courseName={courseMastery.course_name || overview?.chapters?.[0]?.title || `课程 ${courseId}`}
                masteryScore={courseMastery.mastery_score}
                progressPercentage={courseMastery.progress_percentage}
                chaptersCount={courseMastery.chapters_count}
                completedChaptersCount={courseMastery.completed_chapters}
                chapters={courseMastery.chapters}
                onChapterClick={(chapterId) => {
                  const chapter = overview?.chapters?.find(c => c.chapter_id === chapterId);
                  if (chapter) {
                    handleSelectChapter(chapterId, chapter.title);
                  }
                }}
              />
            </div>
          )}

          {/* Legacy Progress Overview (fallback when BKT data not available) */}
          {!courseMastery && overview && (
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
                    {overview.total_mastery_points?.toFixed(0) ?? 0}
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
                    <div className="mt-3 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all"
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
