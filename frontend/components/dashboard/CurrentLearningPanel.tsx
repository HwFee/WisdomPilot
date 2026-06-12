'use client'

import { Panel, PanelHeader, CourseListItem } from '@/components/layout'
import type { CourseProgress } from '@/lib/api/courses'

interface CurrentLearningPanelProps {
  courses: CourseProgress[]
  lang?: 'zh' | 'en'
}

export function CurrentLearningPanel({
  courses,
  lang = 'zh'
}: CurrentLearningPanelProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <Panel>
      <PanelHeader
        title={t('学习进度', 'Learning Progress')}
        count={t(`${courses.length} 门课程`, `${courses.length} courses`)}
      />
      <div>
        {courses.length === 0 ? (
          <div className="px-8 py-6 text-sm text-muted-foreground">
            {t('暂无课程数据', 'No courses available')}
          </div>
        ) : (
          courses.map((course, idx) => (
            <CourseListItem
              key={course.course_id}
              num={String(idx + 1).padStart(2, '0')}
              name={course.course_name}
              chapter={course.current_chapter || course.current_section || t('准备开始', 'Ready to start')}
              percent={Math.round(course.progress)}
              href={`/mastery/${course.course_id}`}
            />
          ))
        )}
      </div>
    </Panel>
  )
}
