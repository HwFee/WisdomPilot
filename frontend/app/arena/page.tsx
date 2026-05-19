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
  Terminal,
  Send,
  Star,
  PartyPopper,
  Frown,
  Lock,
  Trophy,
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

// ========================================
// Types
// ========================================

interface Exercise {
  id: number;
  z_id?: string;
  type: "choice" | "programming" | "fill_blank";
  difficulty: number;
  content: {
    text?: string;
    title?: string;
    description?: string;
    options?: string[];
    code_template?: string;
    input_format?: string;
    output_format?: string;
    sample_input?: string;
    sample_output?: string;
    time_limit?: number;
    memory_limit?: number;
    samples?: Array<{ input: string; output: string }>;
  };
  knowledge_points: string[];
  hints?: string[];
  test_cases?: Array<{ input: string; output: string; name?: string }>;
  solution?: {
    answer?: string;
    explanation?: string;
  };
}

interface TestCaseResult {
  passed: boolean;
  input: string;
  expected: string;
  actual: string;
  time?: number;
  memory?: number;
  message?: string;
}

interface ExerciseProgress {
  exercise_id: number;
  exercise_index: number;
  is_completed: boolean;
  is_correct: boolean;
  is_unlocked: boolean;
  saved_code: string;
  current_language: string;
  title: string;
  difficulty: number;
}

interface TestCase {
  input?: string;
  output?: string;
}

interface ProgressExercise {
  exercise_id: number;
  exercise_index: number;
  is_completed: boolean;
  is_correct: boolean;
  is_unlocked: boolean;
  z_id?: string;
  saved_code?: string;
  current_language?: string;
  title?: string;
  difficulty?: number;
  content?: {
    text?: string;
    description?: string;
    code_template?: string;
    samples?: Array<{ input?: string; output?: string }>;
  };
  knowledge_points?: string[];
  test_cases?: TestCase[];
}

interface ChallengeProgressResponse {
  exercises: ProgressExercise[];
  current_index?: number;
  session_id?: string;
}

type FeedbackState = "idle" | "correct" | "wrong";
type RightPanelTab = "code" | "test" | "output";

// ========================================
// Language Configuration
// ========================================

interface LanguageConfig {
  id: number;
  name: string;
  monaco: string;
}

const LANGUAGE_MAP: Record<string, LanguageConfig> = {
  c: { id: 50, name: "C", monaco: "c" },
  cpp: { id: 54, name: "C++", monaco: "cpp" },
  python: { id: 71, name: "Python", monaco: "python" },
  java: { id: 62, name: "Java", monaco: "java" },
  rust: { id: 73, name: "Rust", monaco: "rust" },
};

const LANGUAGE_OPTIONS = Object.entries(LANGUAGE_MAP).map(([key, config]) => ({
  key,
  ...config,
}));

// ========================================
// Result Modal Component
// ========================================

interface ResultModalProps {
  isCorrect: boolean;
  passedCount: number;
  totalCount: number;
  starsEarned: number;
  promoted: boolean;
  demoted: boolean;
  firstTimeCorrect: boolean;
  firstTimeWrong: boolean;
  onStay: () => void;
  onNext: () => void;
  canGoNext: boolean;
}

function ResultModal({
  isCorrect,
  passedCount,
  totalCount,
  starsEarned,
  promoted,
  demoted,
  firstTimeCorrect,
  firstTimeWrong,
  onStay,
  onNext,
  canGoNext,
}: ResultModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div
        className={`bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 transform transition-all ${
          isCorrect ? "border-2 border-[#52C41A]" : "border-2 border-[#E74C3C]"
        }`}
      >
        <div className="text-center">
          {isCorrect ? (
            <>
              <CheckCircle className="size-20 text-[#52C41A] mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-[#52C41A] mb-2">
                太棒了！全部通过
              </h2>
              <p className="text-[#606266] mb-2">
                {firstTimeCorrect && starsEarned > 0 ? (
                  <span className="text-yellow-500 font-medium flex items-center justify-center gap-1">
                    <Star className="size-5 fill-yellow-500" />
                    +{starsEarned}
                  </span>
                ) : (
                  <span className="text-[#909399]">已获得星星</span>
                )}
              </p>
              {promoted && (
                <p className="text-[#E6A23C] font-bold mb-4 flex items-center justify-center gap-1">
                  <PartyPopper className="size-5" />
                  恭喜晋级！
                </p>
              )}
              {!promoted && (
                <p className="text-[#909399] mb-4">
                  继续挑战下一题
                </p>
              )}
            </>
          ) : (
            <>
              <XCircle className="size-20 text-[#E74C3C] mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-[#E74C3C] mb-2">
                答案错误
              </h2>
              <p className="text-[#606266] mb-6">
                通过 {passedCount}/{totalCount} 个测试点
                {firstTimeWrong && starsEarned < 0 && (
                  <span className="text-red-500 ml-2 flex items-center">
                    <Star className="size-4 text-red-400" />
                    {starsEarned}
                  </span>
                )}
              </p>
              {demoted && (
                <p className="text-[#E74C3C] font-bold mb-4 flex items-center justify-center gap-1">
                  <Frown className="size-5" />
                  段位下降...
                </p>
              )}
            </>
          )}

          <div className="flex gap-3 justify-center">
            <button type="button"
              onClick={onStay}
              className="px-6 py-3 bg-white border border-[#E4E7ED] rounded-xl font-medium text-[#303133] hover:bg-[#F5F7FA] transition-colors"
            >
              留在本题
            </button>
            {canGoNext && (
              <button type="button"
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-[#3498DB] to-[#2980B9] text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
              >
                下一题
                <ArrowRight className="size-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ========================================
// Exercise Navigation Component
// ========================================

interface ExerciseNavigationProps {
  exercises: ExerciseProgress[];
  currentIndex: number;
  onSwitch: (index: number) => void;
}

function ExerciseNavigation({
  exercises,
  currentIndex,
  onSwitch,
}: ExerciseNavigationProps) {
  // 显示5个题目，当前题始终在第3个位置（索引2，即中间）
  const MAX_VISIBLE = 5;
  const CENTER_INDEX = 2; // 当前题目在显示区的中间位置

  // 计算显示范围的起始位置
  // currentIndex = start + CENTER_INDEX => start = currentIndex - CENTER_INDEX
  let start = currentIndex - CENTER_INDEX;
  let end = start + MAX_VISIBLE;

  // 边界处理：开头不够时
  if (start < 0) {
    start = 0;
    end = Math.min(exercises.length, MAX_VISIBLE);
  }

  // 边界处理：结尾不够时
  if (end > exercises.length) {
    end = exercises.length;
    start = Math.max(0, end - MAX_VISIBLE);
  }

  const visibleExercises = exercises.slice(start, end);

  return (
    <div className="flex items-center gap-1.5">
      {visibleExercises.map((ex, idx) => {
        const globalIndex = start + idx;
        const isCurrent = globalIndex === currentIndex;

        return (
          <button type="button"
            key={ex.exercise_id}
            onClick={() => ex.is_unlocked && onSwitch(globalIndex)}
            disabled={!ex.is_unlocked}
            title={`第 ${globalIndex + 1} 题: ${ex.title || "未命名"}`}
            className={`rounded-lg text-xs font-bold transition-all duration-300 ease-out ${
              isCurrent
                ? "size-10 bg-[#3498DB] text-white scale-110 shadow-lg z-10"
                : ex.is_correct
                  ? "size-8 bg-[#D4EDDA] text-[#155724] border-2 border-[#28A745]"
                  : ex.is_completed
                    ? "size-8 bg-[#F8D7DA] text-[#721C24] border-2 border-[#DC3545]"
                    : ex.is_unlocked
                      ? "size-8 bg-white text-[#606266] border border-[#E4E7ED] hover:border-[#3498DB]"
                      : "size-8 bg-[#F5F7FA] text-[#C0C4CC] border border-[#E4E7ED] cursor-not-allowed"
            }`}
          >
            {globalIndex + 1}
          </button>
        );
      })}
    </div>
  );
}

// ========================================
// Exercise List Modal Component - 显示所有做过的题目
// ========================================

interface ExerciseListModalProps {
  isOpen: boolean;
  onClose: () => void;
  exercises: ExerciseProgress[];
  currentIndex: number;
  onSwitch: (index: number) => void;
}

function ExerciseListModal({
  isOpen,
  onClose,
  exercises,
  currentIndex,
  onSwitch,
}: ExerciseListModalProps) {
  if (!isOpen) return null;

  const handleSwitch = (index: number) => {
    if (exercises[index]?.is_unlocked) {
      onSwitch(index);
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl p-6 max-w-lg w-full mx-4 max-h-[70vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-[#303133]">题目列表</h3>
          <button type="button"
            onClick={onClose}
            className="text-[#909399] hover:text-[#606266]"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 gap-y-2">
          {exercises.map((ex, index) => (
            <button type="button"
              key={ex.exercise_id}
              onClick={() => handleSwitch(index)}
              disabled={!ex.is_unlocked}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${
                index === currentIndex
                  ? "bg-[#3498DB]/10 border border-[#3498DB]"
                  : ex.is_unlocked
                    ? "hover:bg-[#F5F7FA] border border-transparent"
                    : "opacity-50 cursor-not-allowed border border-transparent"
              }`}
            >
              <span
                className={`size-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                  index === currentIndex
                    ? "bg-[#3498DB] text-white"
                    : ex.is_correct
                      ? "bg-[#D4EDDA] text-[#155724] border-2 border-[#28A745]"
                      : ex.is_completed
                        ? "bg-[#F8D7DA] text-[#721C24] border-2 border-[#DC3545]"
                        : ex.is_unlocked
                          ? "bg-[#E4E7ED] text-[#606266]"
                          : "bg-[#F5F7FA] text-[#C0C4CC]"
                }`}
              >
                {index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-[#303133] truncate">
                  {ex.title || `第 ${index + 1} 题`}
                </div>
                <div className="text-xs text-[#909399]">
                  难度: {"★".repeat(ex.difficulty || 1)}
                  {ex.is_completed && (
                    <span
                      className={`ml-2 ${ex.is_correct ? "text-[#52C41A]" : "text-[#E74C3C]"}`}
                    >
                      {ex.is_correct ? "已答对" : "已答错"}
                    </span>
                  )}
                </div>
              </div>
              {!ex.is_unlocked && (
                <span className="text-xs text-[#C0C4CC] flex items-center gap-1">
                  <Lock className="size-3" />
                  未解锁
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-[#E4E7ED] text-center text-sm text-[#909399]">
          已完成 {exercises.filter((e) => e.is_completed).length} 题
        </div>
      </div>
    </div>
  );
}

// ========================================
// Main Component
// ========================================

const DIFFICULTY_NAMES: Record<number, string> = {
  1: "入门",
  2: "普及-",
  3: "普及/提高-",
  4: "普及+/提高",
  5: "提高+/省选-",
  6: "省选/NOI-",
  7: "NOI",
  8: "NOI+/CTSC",
};

// 内部组件 - 使用 useSearchParams
function ArenaContent() {
  const { push } = useRouter();
  const searchParams = useSearchParams();
  const difficultyFromDashboard = searchParams.get("difficulty");
  const exerciseIndexFromReview = searchParams.get("exerciseIndex"); // 从错题本跳转时的题目索引

  // Arena state
  const [sessionId, setSessionId] = useState<string>("");
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [exerciseProgress, setExerciseProgress] = useState<ExerciseProgress[]>(
    [],
  );
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  // Code state - saved codes per exercise, per language
  const [savedCodes, setSavedCodes] = useState<
    Record<number, Record<string, string>>
  >({});
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState<string>("python");
  const [feedbackState, setFeedbackState] = useState<FeedbackState>("idle");

  // Right panel state
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>("code");
  const [testResults, setTestResults] = useState<TestCaseResult[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [customTestInput, setCustomTestInput] = useState("");
  const [customTestOutput, setCustomTestOutput] = useState<{
    output?: string;
    expected?: string;
    passed?: boolean;
    error?: string;
  } | null>(null);
  const [isCustomRunning, setIsCustomRunning] = useState(false);

  // Result modal state
  const [showResultModal, setShowResultModal] = useState(false);
  const [modalResult, setModalResult] = useState<{
    isCorrect: boolean;
    passedCount: number;
    totalCount: number;
    starsEarned: number;
    promoted: boolean;
    demoted: boolean;
    firstTimeCorrect: boolean;
    firstTimeWrong: boolean;
  } | null>(null);

  // Exercise list modal state
  const [showExerciseList, setShowExerciseList] = useState(false);

  // Tier tracking
  const [tierInfo, setTierInfo] = useState<{
    tier: string;
    sub_tier: number;
    stars: number;
    full_name: string;
  } | null>(null);

  // Core balance for AI hints
  const [coreBalance, setCoreBalance] = useState<number | undefined>(undefined);

  // Exercise content loading state (lite mode: content loaded on demand)
  const [contentLoadingMap, setContentLoadingMap] = useState<Record<number, boolean>>({});
  const [contentErrorMap, setContentErrorMap] = useState<Record<number, string>>({});
  const loadedContentRef = useRef<Set<number>>(new Set()); // tracks which exercises have full content
  const loadingContentRef = useRef<Set<number>>(new Set()); // tracks in-flight loads to prevent duplicates

  // Refs
  const codeRef = useRef(code);
  codeRef.current = code;
  const currentIndexRef = useRef(currentIndex);
  currentIndexRef.current = currentIndex;
  const mountedRef = useRef(true);
  const isMountedRef = useRef(false);
  const sessionStartedAtRef = useRef<number | null>(null);
  const sessionEndedRef = useRef(false);
  const sessionInitializedRef = useRef(false); // 防止 StrictMode 重复初始化
  const currentDifficultyRef = useRef<number>(1); // 当前挑战之路难度等级

  const endTrackedSession = useCallback(() => {

    if (sessionEndedRef.current) {
      return;
    }

    const token = localStorage.getItem("token:v1");
    const startedAt = sessionStartedAtRef.current;


    if (!token || !startedAt) {
      return;
    }

    const durationSeconds = Math.max(
      1,
      Math.round((Date.now() - startedAt) / 1000),
    );
    const durationMinutes = (durationSeconds / 60).toFixed(1);

    sessionEndedRef.current = true;

    // Use keepalive fetch so the request survives page navigation / unmount.
    endLearningSessionKeepalive(token, durationSeconds, undefined);
  }, []);

  // ========================================
  // Data Fetching
  // ========================================

  const initChallenge = useCallback(async () => {
    const token = localStorage.getItem("token:v1");
    if (!token) {
      push("/login");
      return;
    }

    const difficulty = difficultyFromDashboard
      ? parseInt(difficultyFromDashboard)
      : 1;
    currentDifficultyRef.current = difficulty;

    try {
      setLoading(true);

      // 并行获取：挑战进度 + 段位信息 + 智核余额 + 学习会话
      const parallelTasks: Promise<unknown>[] = [
        getChallengeProgress(token).catch(() => null),
        getGlobalTierInfo().catch(() => null),
        getCoreBalance().catch(() => null),
      ];

      // 学习会话也并行启动，不阻塞核心数据加载
      if (!sessionInitializedRef.current) {
        parallelTasks.push(
          startStageSession(token, 0)
            .then(() => {
              const now = Date.now();
              sessionStartedAtRef.current = now;
              sessionEndedRef.current = false;
              sessionInitializedRef.current = true;
            })
            .catch((error) => {
              console.error("[学习时长] 启动会话失败:", error);
            }),
        );
      }

      const [progressData, tierData, balanceData] = await Promise.all(parallelTasks) as [
        ChallengeProgressResponse | null,
        { tier: string; sub_tier: number; stars: number; full_name: string } | null,
        { balance: number } | null,
      ];

      if (!mountedRef.current) return;

      // 处理段位和智核
      if (tierData) {
        setTierInfo({
          tier: tierData.tier,
          sub_tier: tierData.sub_tier,
          stars: tierData.stars,
          full_name: tierData.full_name,
        });
      }
      if (balanceData) {
        setCoreBalance(balanceData.balance);
      }

      // 先确定语言：优先用 localStorage 中保存的偏好，否则默认 python
      // 必须在 processProgressData 之前，否则 savedCodes 初始化会用错误的 language key
      const savedLanguage = localStorage.getItem("preferred_language");
      const effectiveLanguage =
        savedLanguage && LANGUAGE_MAP[savedLanguage] ? savedLanguage : "python";
      if (effectiveLanguage !== language) {
        setLanguage(effectiveLanguage);
      }

      // 处理挑战进度
      if (progressData && progressData.exercises && progressData.exercises.length > 0) {
        processProgressData(progressData, difficulty, effectiveLanguage);
      } else {
        // 没有练习题，初始化挑战之路
        const sessionData = await startInfiniteSession(
          {
            difficulty_level: difficulty,
            initial_count: 3,
          },
          token,
        );

        if (!mountedRef.current) return;

        // 直接从 startInfiniteSession 响应构建进度数据，避免再次请求
        if (sessionData.exercises && sessionData.exercises.length > 0) {
          const builtProgress: ChallengeProgressResponse = {
            exercises: sessionData.exercises.map((ex: ChallengeExercise, i: number) => ({
              exercise_id: ex.id,
              exercise_index: i,
              is_completed: false,
              is_correct: false,
              is_unlocked: i === 0,
              z_id: ex.z_id,
              saved_code: "",
              current_language: "python",
              title: ex.title || `题目 ${i + 1}`,
              difficulty: ex.difficulty,
              content: ex.content,
              knowledge_points: ex.knowledge_points || [],
              test_cases: ex.test_cases || [],
            })),
            current_index: 0,
            session_id: sessionData.session_id,
          };
          processProgressData(builtProgress, difficulty, effectiveLanguage);
        } else {
          const newProgressData = await getChallengeProgress(token);
          if (!mountedRef.current) return;
          processProgressData(newProgressData, difficulty, effectiveLanguage);
        }
      }
    } catch (error) {
      if (mountedRef.current) {
        console.error("Failed to initialize challenge:", error);
        push("/dashboard");
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [push, difficultyFromDashboard]);

  // 处理进度数据的辅助函数
  const processProgressData = (
    progressData: ChallengeProgressResponse,
    difficulty: number,
    effectiveLanguage: string = language,
  ) => {
    setCurrentIndex(progressData.current_index || 0);
    // 保存 session_id 用于收藏
    if (progressData.session_id) {
      setSessionId(progressData.session_id);
    }

    // 判断是否是 lite 模式（无 content 字段）
    const isLite = progressData.exercises.length > 0 && !progressData.exercises[0]?.content;

    // 转换练习题格式 - lite 模式下 content 为空占位
    const exerciseList: Exercise[] = progressData.exercises.map((ex: ProgressExercise) => {
      const testCases = ex.test_cases || [];
      const samples = ex.content?.samples || [];
      const sampleInput = samples[0]?.input || testCases[0]?.input || "";
      const sampleOutput = samples[0]?.output || testCases[0]?.output || "";
      return {
        id: ex.exercise_id,
        z_id: ex.z_id,
        type: ((ex as ProgressExercise & { type?: string }).type || "programming") as Exercise["type"],
        difficulty: ex.difficulty || difficulty,
        content: isLite ? {
          title: ex.title,
          description: "",
          code_template: getTemplate(effectiveLanguage),
          sample_input: "",
          sample_output: "",
          samples: [],
        } : {
          text: ex.content?.text || ex.title,
          title: ex.title,
          description: ex.content?.description || ex.content?.text || ex.title,
          code_template: ex.content?.code_template || getTemplate(effectiveLanguage),
          sample_input: sampleInput,
          sample_output: sampleOutput,
          samples: samples.map((s: { input?: string; output?: string }) => ({
            input: s.input || "",
            output: s.output || "",
          })),
        },
        knowledge_points: ex.knowledge_points || [],
        test_cases: testCases.map((tc: TestCase) => ({
          input: tc.input || "",
          output: tc.output || "",
        })),
      };
    });

    setExercises(exerciseList);

    // 设置进度信息
    const initialProgress: ExerciseProgress[] = progressData.exercises.map(
      (ex: ProgressExercise) => ({
        exercise_id: ex.exercise_id,
        exercise_index: ex.exercise_index,
        is_completed: ex.is_completed,
        is_correct: ex.is_correct,
        is_unlocked: ex.is_unlocked,
        saved_code: ex.saved_code || "",
        current_language: ex.current_language || "python",
        title: ex.title || `题目 ${ex.exercise_index + 1}`,
        difficulty: ex.difficulty || 1,
      }),
    );
    setExerciseProgress(initialProgress);

    // 初始化保存的代码：用当前语言作为 key（之前硬编码为 "python" 导致切换语言后取不到）
    const initialCodes: Record<number, Record<string, string>> = {};
    progressData.exercises.forEach((ex: ProgressExercise) => {
      initialCodes[ex.exercise_id] = {
        [effectiveLanguage]:
          ex.saved_code || ex.content?.code_template || getTemplate(effectiveLanguage),
      };
    });
    setSavedCodes(initialCodes);

    // 处理从错题本跳转的情况
    const targetIndex = exerciseIndexFromReview
      ? parseInt(exerciseIndexFromReview)
      : progressData.current_index || 0;
    const validIndex = Math.min(
      Math.max(0, targetIndex),
      exerciseList.length - 1,
    );

    if (exerciseList.length > 0) {
      setCurrentIndex(validIndex);
      const savedCode =
        initialCodes[exerciseList[validIndex].id]?.[effectiveLanguage] ||
        exerciseList[validIndex].content.code_template ||
        getTemplate(effectiveLanguage);
      setCode(savedCode);

      // Lite 模式下：立即按需加载当前题目的完整内容
      if (isLite) {
        loadExerciseContent(exerciseList[validIndex].id, validIndex);
      }
    }
  };

  // 按需加载单个题目的完整内容（lite 模式优化）
  const loadExerciseContent = async (exerciseId: number, index: number) => {
    // Prevent duplicate in-flight requests
    if (loadingContentRef.current.has(exerciseId)) return;
    if (loadedContentRef.current.has(exerciseId)) return;

    const token = localStorage.getItem("token:v1");
    if (!token) return;

    loadingContentRef.current.add(exerciseId);
    setContentLoadingMap((prev) => ({ ...prev, [exerciseId]: true }));
    setContentErrorMap((prev) => {
      const next = { ...prev };
      delete next[exerciseId];
      return next;
    });

    try {
      const data = await getChallengeExerciseContent(exerciseId, token);
      loadedContentRef.current.add(exerciseId);

      if (!mountedRef.current) return;

      const exercise = data.exercise;
      const samples = exercise.content?.samples || [];
      const sampleInput = samples[0]?.input || "";
      const sampleOutput = samples[0]?.output || "";

      setExercises((prev) => {
        const updated = [...prev];
        if (updated[index]) {
          updated[index] = {
            ...updated[index],
            type: (exercise.type || updated[index].type) as Exercise["type"],
            content: {
              text: exercise.content?.text || updated[index].content.title,
              title: exercise.title || updated[index].content.title,
              description: exercise.content?.description || exercise.content?.text || updated[index].content.title,
              code_template: exercise.content?.code_template || getTemplate("python"),
              sample_input: sampleInput,
              sample_output: sampleOutput,
              samples: samples.map((s: { input?: string; output?: string }) => ({
                input: s.input || "",
                output: s.output || "",
              })),
            },
            knowledge_points: exercise.knowledge_points || [],
            test_cases: (exercise.test_cases || []).map((tc: { input?: string; output?: string }) => ({
              input: tc.input || "",
              output: tc.output || "",
            })),
          };
        }
        return updated;
      });

      // Use ref to check current index (avoids stale closure)
      if (index === currentIndexRef.current) {
        setSavedCodes((prev) => {
          const updated = { ...prev };
          const existingCode = updated[exerciseId]?.[language];
          // 只在没有保存代码时才使用模板
          if (!existingCode || existingCode === getTemplate("python")) {
            updated[exerciseId] = {
              ...updated[exerciseId],
              [language]: exercise.content?.code_template || getTemplate(language),
            };
            setCode(exercise.content?.code_template || getTemplate(language));
          }
          return updated;
        });
      }
    } catch (error) {
      console.error("[挑战之路] 加载题目内容失败:", error);
      const errorMsg = error instanceof Error ? error.message : "加载失败";
      setContentErrorMap((prev) => ({ ...prev, [exerciseId]: errorMsg }));
      // Remove from loaded set so retry can happen
      loadedContentRef.current.delete(exerciseId);
    } finally {
      loadingContentRef.current.delete(exerciseId);
      if (mountedRef.current) {
        setContentLoadingMap((prev) => {
          const next = { ...prev };
          delete next[exerciseId];
          return next;
        });
      }
    }
  };

  useEffect(() => {
    initChallenge();
  }, [initChallenge]);

  // ========================================
  // Language helpers
  // ========================================

  const getLanguageId = () => LANGUAGE_MAP[language]?.id || 71;

  const handleLanguageChange = (newLang: string) => {
    if (newLang === language) return;

    const currentExercise = exercises[currentIndex];
    if (!currentExercise) return;

    // Save current code for current language
    setSavedCodes((prev) => ({
      ...prev,
      [currentExercise.id]: {
        ...prev[currentExercise.id],
        [language]: codeRef.current,
      },
    }));

    // Switch language
    setLanguage(newLang);
    localStorage.setItem("preferred_language", newLang);

    // Restore code for new language or use template
    const savedCodeForNewLang = savedCodes[currentExercise.id]?.[newLang];
    if (savedCodeForNewLang) {
      setCode(savedCodeForNewLang);
    } else {
      setCode(getTemplate(newLang));
    }

    // Save to backend (无 session 概念，独立于课程)
    const token = localStorage.getItem("token:v1");
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

  const handleCustomRun = async (
    input: string,
    isFromSample: boolean = false,
  ) => {
    if (!code || isCustomRunning) return;

    setIsCustomRunning(true);
    setCustomTestOutput(null);
    if (isFromSample) {
      setRightPanelTab("test");
    }

    try {
      const token = localStorage.getItem("token:v1");
      if (!token) return;

      const result = await executeCode(
        {
          code: code,
          language_id: getLanguageId(),
          stdin: input,
        },
        token,
      );

      setCustomTestOutput({
        output: result.stdout || "",
        expected: undefined,
        passed: undefined,
        error: result.stderr || result.compile_output,
      });
    } catch (error) {
      console.error("Custom run failed:", error);
      setCustomTestOutput({ error: "运行失败，请重试" });
    } finally {
      setIsCustomRunning(false);
    }
  };

  const handleSampleRun = async (input: string, expectedOutput?: string) => {
    setCustomTestInput(input);

    if (!code || isCustomRunning) return;

    setIsCustomRunning(true);
    setCustomTestOutput(null);
    setRightPanelTab("test");

    try {
      const token = localStorage.getItem("token:v1");
      if (!token) return;

      const result = await executeCode(
        {
          code: code,
          language_id: getLanguageId(),
          stdin: input,
        },
        token,
      );

      const output = (result.stdout || "").trim();
      const expected = (expectedOutput || "").trim();
      const passed = output === expected;

      setCustomTestOutput({
        output: output,
        expected: expected,
        passed: passed,
        error: result.stderr || result.compile_output,
      });
    } catch (error) {
      console.error("Sample run failed:", error);
      setCustomTestOutput({ error: "运行失败，请重试" });
    } finally {
      setIsCustomRunning(false);
    }
  };

  // ========================================
  // Submit
  // ========================================

  const handleSubmit = async () => {
    if (!exercises[currentIndex] || isSubmitting) return;

    const currentExercise = exercises[currentIndex];

    setIsSubmitting(true);
    setTestResults([]);
    setRightPanelTab("output");

    try {
      const token = localStorage.getItem("token:v1");
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
      setSavedCodes((prev) => ({
        ...prev,
        [currentExercise.id]: {
          ...prev[currentExercise.id],
          [language]: code,
        },
      }));

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
            const newExercises: Exercise[] = newProgressData.exercises
              .filter(
                (ex: ProgressExercise) =>
                  !exercises.find((e) => e.id === ex.exercise_id),
              )
              .map((ex: ProgressExercise) => {
                return {
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
                };
              });

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
              if (!savedCodes[ex.exercise_id]) {
                newSavedCodes[ex.exercise_id] = {
                  python: ex.saved_code || getTemplate("python"),
                };
              }
            });
            setSavedCodes((prev) => ({ ...prev, ...newSavedCodes }));
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

  const switchToExercise = useCallback(
    async (index: number) => {
      if (index < 0 || index >= exercises.length) return;

      const currentExercise = exercises[currentIndex];
      const targetExercise = exercises[index];

      // Check if unlocked
      const targetProgress = exerciseProgress.find(
        (p) => p.exercise_id === targetExercise.id,
      );
      if (targetProgress && !targetProgress.is_unlocked) {
        return; // Can't switch to locked exercise
      }

      // Save current code
      if (currentExercise) {
        setSavedCodes((prev) => ({
          ...prev,
          [currentExercise.id]: {
            ...prev[currentExercise.id],
            [language]: codeRef.current,
          },
        }));
      }

      setCurrentIndex(index);

      // Restore code for target exercise
      const savedCodeForLang = savedCodes[targetExercise.id]?.[language];
      if (savedCodeForLang) {
        setCode(savedCodeForLang);
      } else {
        setCode(targetExercise.content.code_template || getTemplate(language));
      }

      // 按需加载目标题目的完整内容（如果是 lite 模式还没加载过的）
      if (!loadedContentRef.current.has(targetExercise.id) && !loadingContentRef.current.has(targetExercise.id)) {
        loadExerciseContent(targetExercise.id, index);
      }

      setTestResults([]);
      setFeedbackState("idle");
      setRightPanelTab("code");
      setCustomTestOutput(null);
      setShowResultModal(false);
    },
    [exercises, currentIndex, exerciseProgress, savedCodes, language],
  );

  const handleNext = useCallback(() => {
    setShowResultModal(false);
    if (currentIndex < exercises.length - 1) {
      switchToExercise(currentIndex + 1);
    }
  }, [currentIndex, exercises.length, switchToExercise]);

  const handleStay = useCallback(() => {
    setShowResultModal(false);
  }, []);

  const handleRetry = useCallback(() => {
    setTestResults([]);
    setFeedbackState("idle");
    setCustomTestOutput(null);
    setRightPanelTab("code");
    setShowResultModal(false);
  }, []);

  // ========================================
  // Exit
  // ========================================

  const handleExitSave = useCallback(async () => {
    const token = localStorage.getItem("token:v1");
    const currentExercise = exercises[currentIndex];

    if (token && currentExercise) {
      try {
        await saveChallengeCode(
          {
            exercise_id: currentExercise.id,
            code: codeRef.current,
            language: language,
          },
          token,
        );
      } catch (error) {
        console.error("Failed to save on exit:", error);
      }
    }
  }, [exercises, currentIndex, language]);

  // Cleanup on unmount
  // 使用 isMountedRef 来区分 StrictMode 的假 unmount 和真正的 unmount
  useEffect(() => {
    mountedRef.current = true;
    isMountedRef.current = true;

    return () => {
      mountedRef.current = false;

      // StrictMode 下，cleanup 会立即执行，然后重新 mount
      // 使用 requestAnimationFrame 或 setTimeout 来延迟执行
      // 如果很快重新 mount，则 isMountedRef 会变回 true
      isMountedRef.current = false;
      // 重置 session 初始化标记，允许重新进入页面时重新初始化
      sessionInitializedRef.current = false;

      // 延迟执行 endTrackedSession，给 StrictMode 重新 mount 的机会
      requestAnimationFrame(() => {
        if (!isMountedRef.current) {
          endTrackedSession();
        }
      });
    };
  }, [endTrackedSession]);

  const handleExit = async () => {
    await handleExitSave();
    endTrackedSession();
    push("/dashboard");
  };

  // ========================================
  // Difficulty names
  // ========================================
  // Loading State
  // ========================================

  if (loading && exercises.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white to-[#F7F8FA] flex flex-col">
        <header className="h-[50px] bg-white border-b border-[#E4E7ED] flex items-center justify-between px-4">
          <div className="skeleton h-8 w-32 rounded-lg"></div>
          <div className="flex items-center gap-4">
            <div className="skeleton h-6 w-40 rounded-lg"></div>
            <div className="skeleton h-8 w-20 rounded-full"></div>
          </div>
        </header>
        <main className="flex-1 flex pt-[50px]">
          <div className="w-[40%] border-r border-[#E4E7ED] p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="skeleton h-8 w-20 rounded-lg"></div>
              <div className="skeleton h-6 w-16 rounded-lg"></div>
            </div>
            <div className="skeleton h-7 w-3/4 rounded mb-4"></div>
            <div className="gap-y-3">
              <div className="skeleton h-4 w-full rounded"></div>
              <div className="skeleton h-4 w-full rounded"></div>
              <div className="skeleton h-4 w-2/3 rounded"></div>
            </div>
          </div>
          <div className="w-[60%] flex flex-col">
            <div className="h-12 bg-[#F5F7FA] border-b border-[#E4E7ED] flex items-center gap-2 px-4">
              <div className="skeleton h-8 w-16 rounded"></div>
              <div className="skeleton h-8 w-16 rounded"></div>
            </div>
            <div className="flex-1 bg-white">
              <div className="skeleton h-full w-full"></div>
            </div>
          </div>
        </main>
        <div className="h-[72px] bg-white border-t border-[#E4E7ED] flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="skeleton size-8 rounded-lg"></div>
            <div className="skeleton h-4 w-32 rounded"></div>
          </div>
          <div className="flex gap-2">
            <div className="skeleton h-10 w-20 rounded-lg"></div>
            <div className="skeleton h-10 w-24 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  // ========================================
  // Main IDE View
  // ========================================

  if (exercises.length === 0) return null;

  const currentExercise = exercises[currentIndex];
  const currentProgress = exerciseProgress.find(
    (p) => p.exercise_id === currentExercise.id,
  );
  const isLastExercise = currentIndex === exercises.length - 1;
  const passedCount = testResults.filter((r) => r.passed).length;
  const canGoNext =
    currentIndex < exercises.length - 1 &&
    exerciseProgress[currentIndex + 1]?.is_unlocked;

  return (
    <div className="min-h-screen ide-container flex flex-col">
      {/* Top Bar */}
      <header className="fixed top-0 left-0 right-0 z-50 h-[50px] ide-header">
        <div className="h-full px-4 flex items-center justify-between">
          <button type="button" onClick={handleExit} className="ide-header-back">
            <X className="size-4" />
            <span className="text-sm">退出挑战</span>
          </button>

          <div className="flex items-center gap-4">
            {/* Exercise Navigation */}
            <ExerciseNavigation
              exercises={exerciseProgress}
              currentIndex={currentIndex}
              onSwitch={switchToExercise}
            />

            {/* 题目列表按钮 */}
            <button type="button"
              onClick={() => setShowExerciseList(true)}
              className="px-3 py-1.5 bg-white border border-[#E4E7ED] rounded-lg text-xs text-[#606266] hover:border-[#3498DB] hover:text-[#3498DB] transition-colors flex items-center gap-1.5"
            >
              <span>题目列表</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex pt-[50px] h-[calc(100vh-50px)] overflow-hidden">
        {/* Left: Problem Panel */}
        <div
          className="w-[40%] ide-problem-panel bg-white flex-shrink-0"
          style={{
            maxHeight: "calc(100vh - 50px)",
            overflowY: "auto",
            overflowX: "hidden",
          }}
        >
          {currentExercise && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-lg text-xs font-bold text-white difficulty-badge difficulty-${currentExercise.difficulty}`}
                  >
                    {DIFFICULTY_NAMES[currentExercise.difficulty] ||
                      `难度 ${currentExercise.difficulty}`}
                  </span>
                  <span className="text-base font-medium text-[#303133]">
                    {currentExercise.z_id && (
                      <span className="text-[#909399] mr-2 font-normal">{currentExercise.z_id}</span>
                    )}
                    {currentExercise.content.title || `题目 ${currentIndex + 1}`}
                  </span>
                </div>
                {/* 收藏按钮 */}
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
                  size="md"
                  showLabel
                />
              </div>

              {contentLoadingMap[currentExercise.id] ? (
                <div className="mb-6 p-4 bg-[#F5F7FA] rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-[#909399]">
                    <Loader2 className="size-4 animate-spin" />
                    正在加载题面...
                  </div>
                </div>
              ) : contentErrorMap[currentExercise.id] ? (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-red-600 mb-2">
                    <AlertTriangle className="size-4" />
                    题面加载失败
                  </div>
                  <p className="text-xs text-red-500 mb-3">{contentErrorMap[currentExercise.id]}</p>
                  <button
                    type="button"
                    onClick={() => loadExerciseContent(currentExercise.id, currentIndex)}
                    className="px-3 py-1.5 bg-white border border-red-300 text-red-600 text-xs rounded-md hover:bg-red-50 transition-colors"
                  >
                    重试
                  </button>
                </div>
              ) : currentExercise.content.description ? (
                <div className="text-[#606266] leading-relaxed mb-6">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      h1: ({ children }) => <h1 className="text-xl font-semibold text-[#303133] mb-2 mt-4">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-semibold text-[#303133] mt-4 mb-2 border-b border-[#E4E7ED] pb-2">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-base font-semibold text-[#303133] mt-3 mb-2">{children}</h3>,
                      p: ({ children }) => <p className="text-[#606266] mb-2 leading-relaxed">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside gap-y-1 my-2 ml-2">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside gap-y-1 my-2 ml-2">{children}</ol>,
                      li: ({ children }) => <li className="text-[#606266]">{children}</li>,
                      blockquote: ({ children }) => <blockquote className="border-l-4 border-primary/30 pl-4 italic my-2 text-[#606266]">{children}</blockquote>,
                      strong: ({ children }) => <strong className="font-semibold text-[#303133]">{children}</strong>,
                      code: ({ className, children, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                          <code className="bg-[#F5F7FA] px-1.5 py-0.5 rounded text-sm text-[#E74C3C] font-mono border border-[#E4E7ED]" {...props}>
                            {children}
                          </code>
                        ) : (
                          <code className={className} {...props}>{children}</code>
                        );
                      },
                      pre: ({ children }) => (
                        <pre
                          className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3"
                          style={{ backgroundColor: '#1e293b', color: '#e2e8f0', border: '1px solid #334155' }}
                        >
                          {children}
                        </pre>
                      ),
                      table: ({ children }) => (
                        <div className="overflow-x-auto my-3">
                          <table className="min-w-full border-collapse border border-[#E4E7ED]">{children}</table>
                        </div>
                      ),
                      thead: ({ children }) => <thead className="bg-[#F5F7FA]">{children}</thead>,
                      th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-[#303133] border border-[#E4E7ED]">{children}</th>,
                      td: ({ children }) => <td className="px-3 py-2 text-sm text-[#606266] border border-[#E4E7ED]">{children}</td>,
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
                  {currentExercise.knowledge_points.map((kp, i) => (
                    <span
                      key={`arena-${i}`}
                      className="knowledge-tag px-3 py-1.5 text-[#3498DB] text-xs rounded-lg font-medium"
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
                    exercise_id: String(currentExercise.id),  // 使用题目 ID 作为唯一标识
                    exercise_title: currentExercise.content.title || `题目 #${currentExercise.id}`,
                    exercise_description: currentExercise.content.description || currentExercise.content.text || "",
                    difficulty: currentExercise.difficulty,
                    knowledge_points: currentExercise.knowledge_points || [],
                    code_template: currentExercise.content.code_template,
                    sample_input: currentExercise.content.sample_input,
                    sample_output: currentExercise.content.sample_output,
                  }}
                  token={localStorage.getItem("token:v1") || ""}
                  onBalanceChange={async () => {
                    // 刷新智核余额
                    const token = localStorage.getItem("token:v1");
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
          )}
        </div>

        {/* Right: Code Editor + Test Panel */}
        <div
          className="w-[60%] flex flex-col ide-editor-panel bg-white flex-shrink-0"
          style={{ maxHeight: "calc(100vh - 50px)", overflow: "hidden" }}
        >
          {/* Tab Header */}
          <div className="panel-tabs flex-shrink-0 flex items-center justify-between">
            <div className="flex">
              <button type="button"
                onClick={() => setRightPanelTab("code")}
                className={`panel-tab ${rightPanelTab !== "output" ? "active" : ""}`}
              >
                <Code2 className="size-4 inline mr-1.5" />
                代码
              </button>
              {testResults.length > 0 && (
                <button type="button"
                  onClick={() => setRightPanelTab("output")}
                  className={`panel-tab ${rightPanelTab === "output" ? "active" : ""}`}
                >
                  <CheckCircle className="size-4 inline mr-1.5" />
                  结果
                </button>
              )}
            </div>
            <div className="flex items-center gap-2 pr-3">
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="px-2 py-1 text-xs font-medium text-[#606266] bg-white border border-[#E4E7ED] rounded-md focus:outline-none focus:border-[#3498DB] cursor-pointer"
              >
                {LANGUAGE_OPTIONS.map((lang) => (
                  <option key={lang.key} value={lang.key}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Content: code + test stacked, or output tab */}
          <div className="flex-1 overflow-hidden">
            {rightPanelTab === "output" && testResults.length > 0 ? (
              <div className="h-full overflow-y-auto p-4 bg-[#FAFBFC]">
                <LuoguTestCaseTable
                  results={testResults}
                  passedCount={passedCount}
                  totalCount={testResults.length}
                  isRunning={isSubmitting}
                />
              </div>
            ) : (
              <div className="h-full flex flex-col">
                {/* Code editor - upper part */}
                <div className="flex-1 min-h-0">
                  <CodeEditorPanel
                    value={code}
                    onChange={setCode}
                    language={LANGUAGE_MAP[language]?.monaco || "python"}
                  />
                </div>
                {/* Test panel - below code */}
                <div className="h-[220px] flex-shrink-0 border-t border-[#E4E7ED] bg-[#FAFBFC] overflow-y-auto">
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
                  <div className="size-10 bg-[#3498DB]/10 rounded-lg flex items-center justify-center border border-[#3498DB]/20">
                    <Zap className="size-5 text-[#F39C11]" />
                  </div>
                  <div>
                    <p className="text-sm text-[#303133] font-medium">
                      挑战之路
                    </p>
                    <p className="text-xs text-[#909399]">
                      {tierInfo ? (
                        <>
                          当前段位{" "}
                          <span className="font-medium" style={{ color: TIER_COLORS[tierInfo.tier as keyof typeof TIER_COLORS] || '#CD7F32' }}>
                            {tierInfo.full_name}
                          </span>
                          {" "}<span className="text-yellow-500 flex items-center inline-flex"><Star className="size-3.5 fill-yellow-500" />{tierInfo.stars}</span>
                        </>
                      ) : (
                        "加载中..."
                      )}
                    </p>
                  </div>
                </div>

                {testResults.length > 0 && (
                  <>
                    <div className="h-6 w-px bg-[#E4E7ED]" />
                    <LuoguTestCasesSummary
                      passedCount={passedCount}
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
                      <Loader2 className="size-4 animate-spin" />
                      提交中...
                    </>
                  ) : (
                    <>
                      <Send className="size-4" />
                      提交
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : feedbackState === "correct" ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-[#52C41A]/10 rounded-lg flex items-center justify-center border border-[#52C41A]/20 success-pulse">
                  <CheckCircle className="size-6 text-[#52C41A]" />
                </div>
                <div>
                  <p className="font-semibold text-[#52C41A]">
                    太棒了！全部通过
                  </p>
                  <p className="text-sm text-[#52C41A]/70">继续挑战下一题</p>
                </div>
              </div>
              <div className="action-buttons-group">
                <button type="button" onClick={handleRetry} className="btn-action btn-reset">
                  <RotateCcw className="size-4" />
                  重新作答
                </button>
                {canGoNext && (
                  <button type="button"
                    onClick={handleNext}
                    className="btn-action btn-success"
                  >
                    下一题
                    <ArrowRight className="size-5" />
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-[#E74C3C]/10 rounded-lg flex items-center justify-center border border-[#E74C3C]/20 error-shake">
                  <XCircle className="size-6 text-[#E74C3C]" />
                </div>
                <div>
                  <p className="font-semibold text-[#E74C3C]">答案错误</p>
                  {testResults.length > 0 && (
                    <p className="text-sm text-[#E74C3C]/70">
                      通过 {passedCount}/{testResults.length} 个测试点 ·
                      修改后重新提交
                    </p>
                  )}
                </div>
              </div>
              <div className="action-buttons-group">
                <button type="button" onClick={handleRetry} className="btn-action btn-reset">
                  <RotateCcw className="size-4" />
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
                    <ArrowRight className="size-5" />
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
        onSwitch={switchToExercise}
      />
    </div>
  );
}

// 主组件 - 用 Suspense 包裹
export default function ArenaPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <Loader2 className="size-8 animate-spin text-primary" />
      </div>
    }>
      <ArenaContent />
    </Suspense>
  );
}
