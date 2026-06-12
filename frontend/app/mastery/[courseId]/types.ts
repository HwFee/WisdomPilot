export type MasteryStep =
  | "select_chapter"
  | "base_quiz"
  | "analysis"
  | "enhanced_quiz"
  | "result";

export const getQuestionType = (
  question: { question_type?: string; type?: string },
): "choice" | "fill_blank" => {
  return (question.question_type || question.type || "choice") as
    | "choice"
    | "fill_blank";
};

export const DIFFICULTY_COLORS: Record<number, string> = {
  1: "bg-muted text-emerald-600 border-emerald-600",
  2: "bg-muted text-emerald-600 border-emerald-600",
  3: "bg-muted text-amber-600 border-amber-600",
  4: "bg-muted text-amber-600 border-amber-600",
  5: "bg-muted text-red-600 border-red-600",
};
