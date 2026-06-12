"use client";

import { ArrowLeft, Trophy, BookOpen, ChevronRight } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import type { MasteryOverviewResponse, CourseDetailResponse, BaseQuestionResponse, MasteryLevel, NoteResponse } from "@/types/api";

import { NoteEditor } from "@/components/notes/NoteEditor";
import { PageContainer, SectionHeader } from "@/components/layout";
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

const GRID_TEMPLATE = "grid-cols-[auto_1fr_auto_auto_auto]";

export function ChapterListView(props: ChapterListViewProps) {
  const {
    overview, courseDetail, onSelectChapter, courseId, selectedChapterId,
    selectedSectionId, baseQuestions, currentQuestionIndex, showNoteEditor,
    editingNote, setShowNoteEditor, setEditingNote, setNoteRefreshKey, noteRefreshKey,
  } = props;

  const chapters = overview?.chapters && overview.chapters.length > 0
    ? overview.chapters
    : courseDetail?.course?.chapters || [];
  const hasChapters = chapters.length > 0;

  return (
    <div className="min-h-screen bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
        <PageContainer className="h-14 flex items-center justify-between">
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
          <div className="w-20" />
        </PageContainer>
      </header>

      <main className="pt-20 pb-12">
        <PageContainer>
          <SectionHeader title="章节列表" />

          {hasChapters ? (
            <div className="bg-card border border-border">
              {/* Header row */}
              <div
                className={`grid ${GRID_TEMPLATE} items-center gap-5 px-8 py-4 border-b border-border bg-muted/50 text-[11px] uppercase tracking-[1.5px] text-muted-foreground font-medium`}
              >
                <span className="w-8">编号</span>
                <span>标题</span>
                <span className="w-[100px] text-center">进度</span>
                <span className="w-12 text-right">百分比</span>
                <span className="w-10 text-right">操作</span>
              </div>

              {chapters.map((chapter) => {
                const isLoggedInChapter = "chapter_id" in chapter;
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
                  <Button
                    type="button"
                    key={chapterId}
                    onClick={() => onSelectChapter(chapterId, title)}
                    variant="ghost"
                    className={`w-full h-auto grid ${GRID_TEMPLATE} items-center gap-5 px-8 py-5 border-b border-border last:border-b-0 text-left hover:bg-muted/30 transition-colors rounded-none`}
                  >
                    <div className="size-10 rounded-lg flex items-center justify-center font-medium bg-secondary text-amber-600">
                      {orderIndex}
                    </div>
                    <div>
                      <div className="text-[15px] font-medium text-foreground">
                        {title}
                      </div>
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
                    <div className="w-[100px] h-[3px] bg-border relative">
                      <div
                        className="absolute left-0 top-0 bottom-0 bg-foreground"
                        style={{ width: `${masteryPercent}%` }}
                      />
                    </div>
                    <span className="font-mono text-[13px] font-semibold w-12 text-right">
                      {masteryPercent.toFixed(0)}%
                    </span>
                    <div className="w-10 flex justify-end">
                      <ChevronRight className="size-5 text-muted-foreground" strokeWidth={1.5} />
                    </div>
                  </Button>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-16 bg-card border border-border">
              <div className="size-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                <BookOpen className="size-8 text-muted-foreground" strokeWidth={1.5} />
              </div>
              <p className="text-muted-foreground">暂无章节内容</p>
            </div>
          )}
        </PageContainer>
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
          onSave={() => {
            setNoteRefreshKey((prev) => prev + 1);
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
