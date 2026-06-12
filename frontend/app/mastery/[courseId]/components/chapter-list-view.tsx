"use client";

import { ArrowLeft, Trophy, BookOpen, ChevronRight } from "lucide-react";
import Link from "next/link";
import type { MasteryOverviewResponse, CourseDetailResponse, BaseQuestionResponse, MasteryLevel, NoteResponse } from "@/types/api";

import { NoteEditor } from "@/components/notes/NoteEditor";
import { getStoredToken, MASTERY_LEVEL_COLORS } from "@/lib/api";

interface ChapterListViewProps {
  overview: MasteryOverviewResponse | null;
  courseDetail: CourseDetailResponse | null;
  onSelectChapter: (chapterId: number, title: string) => void;
  courseId: number;
  selectedChapterId: number | null;
  selectedSectionId: number | null;
  baseQuestions: BaseQuestionResponse[];
  currentQuestionIndex: number;
  showNoteEditor: boolean;
  editingNote: NoteResponse | null;
  setShowNoteEditor: React.Dispatch<React.SetStateAction<boolean>>;
  setEditingNote: React.Dispatch<React.SetStateAction<NoteResponse | null>>;
  setNoteRefreshKey: React.Dispatch<React.SetStateAction<number>>;
  noteRefreshKey: number;
}

export function ChapterListView(props: ChapterListViewProps) {
  const {
    overview, courseDetail, onSelectChapter, courseId, selectedChapterId,
    selectedSectionId, baseQuestions, currentQuestionIndex, showNoteEditor,
    editingNote, setShowNoteEditor, setEditingNote, setNoteRefreshKey, noteRefreshKey,
  } = props;

  return (
  <div className="min-h-screen bg-background">
    <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
    <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
      <Link
        href={getStoredToken() ? "/dashboard" : "/"}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="size-4" strokeWidth={1.5} />
        <span className="text-sm">返回</span>
      </Link>
      <div className="flex items-center gap-2">
        <Trophy className="size-5 text-amber-600" strokeWidth={1.5} />
        <span className="font-semibold">精进之路</span>
      </div>
      <div className="w-20"></div>
    </div>
    </header>

    <main className="pt-20 pb-12 px-4">
    <div className="max-w-4xl mx-auto">
      {/* Chapter List */}
      <h3 className="text-lg font-semibold text-foreground mb-4">
        选择章节开始学习
      </h3>

      {/* 优先使用 overview（登录后有掌握度），否则使用 courseDetail（未登录） */}
      {(overview?.chapters && overview.chapters.length > 0) ||
      (courseDetail?.course?.chapters && courseDetail.course.chapters.length > 0) ? (
        <div className="flex flex-col gap-y-3">
          {(overview?.chapters || courseDetail?.course?.chapters || []).map((chapter) => {
            // 登录状态：从 overview 获取，有掌握度数据
            // 未登录状态：从 courseDetail 获取，只有基础信息
            const isLoggedInChapter = 'chapter_id' in chapter;
            const chapterId = isLoggedInChapter
              ? (chapter as { chapter_id: number }).chapter_id
              : (chapter as { id: number }).id;
            const orderIndex = (chapter as { order_index: number }).order_index;
            const title = chapter.title;
            const masteryPercent = isLoggedInChapter
              ? ((chapter as { mastery_score?: number }).mastery_score ?? 0)
              : 0;
            const masteryLevel = isLoggedInChapter
              ? ((chapter as { mastery_level?: string }).mastery_level as MasteryLevel)
              : null;

            return (
              <button type="button"
                key={chapterId}
                onClick={() =>
                  onSelectChapter(chapterId, title)
                }
                className="w-full p-4 rounded-lg border text-left transition-colors border-border hover:border-primary hover:bg-muted"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="size-10 rounded-lg flex items-center justify-center font-medium bg-secondary text-amber-600"
                    >
                      {orderIndex}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">
                        {title}
                      </p>
                      {masteryLevel && (
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
                      )}
                    </div>
                  </div>
                  <ChevronRight className="size-5 text-muted-foreground" strokeWidth={1.5} />
                </div>

                {/* Progress bar - 仅登录时显示 */}
                {masteryLevel && (
                  <div className="mt-3 h-1.5 bg-muted rounded-lg overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-lg transition-all"
                      style={{ width: `${masteryPercent}%` }}
                    />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 bg-card rounded-lg border border-border">
          <div className="size-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
            <BookOpen className="size-8 text-muted-foreground" strokeWidth={1.5} />
          </div>
          <p className="text-muted-foreground">暂无章节内容</p>
        </div>
      )}
    </div>
    </main>

    {/* Note Editor Modal */}
    {showNoteEditor && (
    <NoteEditor
      note={editingNote}
      exerciseId={baseQuestions[currentQuestionIndex]?.id}
      courseId={courseId}
      chapterId={selectedChapterId || undefined}
      sectionId={selectedSectionId || undefined}
      knowledgePoints={baseQuestions[currentQuestionIndex]?.knowledge_points}
      prefillContent={baseQuestions[currentQuestionIndex]?.text}
      prefillTitle={baseQuestions[currentQuestionIndex]?.text ? `题目笔记: ${baseQuestions[currentQuestionIndex].text.slice(0, 30)}...` : undefined}
      source="question"
      onSave={(savedNote) => {
      }}
      onClose={() => {
        setShowNoteEditor(false);
        setEditingNote(null);
      }}
    />
    )}
  </div>
  );
}
