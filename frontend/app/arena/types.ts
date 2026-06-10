export interface Exercise {
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

export interface TestCaseResult {
  passed: boolean;
  input: string;
  expected: string;
  actual: string;
  time?: number;
  memory?: number;
  message?: string;
}

export interface ExerciseProgress {
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

export interface TestCase {
  input?: string;
  output?: string;
}

export interface ProgressExercise {
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
  solution?: {
    answer?: string;
    explanation?: string;
  };
}

export interface ChallengeProgressResponse {
  exercises: ProgressExercise[];
  current_index?: number;
  session_id?: string;
}

export type FeedbackState = "idle" | "correct" | "wrong";
export type RightPanelTab = "code" | "test" | "output";

export interface LanguageConfig {
  id: number;
  name: string;
  monaco: string;
}

export const LANGUAGE_MAP: Record<string, LanguageConfig> = {
  c: { id: 50, name: "C", monaco: "c" },
  cpp: { id: 54, name: "C++", monaco: "cpp" },
  python: { id: 71, name: "Python", monaco: "python" },
  java: { id: 62, name: "Java", monaco: "java" },
  rust: { id: 73, name: "Rust", monaco: "rust" },
};

export const LANGUAGE_OPTIONS = Object.entries(LANGUAGE_MAP).map(([key, config]) => ({
  key,
  ...config,
}));

export const DIFFICULTY_NAMES: Record<number, string> = {
  1: "入门",
  2: "普及-",
  3: "普及/提高-",
  4: "普及+/提高",
  5: "提高+/省选-",
  6: "省选/NOI-",
  7: "NOI",
  8: "NOI+/CTSC",
};
