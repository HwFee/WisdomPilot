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
  1: "bg-green-500/20 text-green-400 border-green-500/30",
  2: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  3: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  4: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  5: "bg-red-500/20 text-red-400 border-red-500/30",
};
