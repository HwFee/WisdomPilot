import Link from 'next/link'
import { getCourseConfig } from '@/lib/icons/course-icons'
import { cn } from '@/lib/utils'

interface CourseCardData {
  id: number
  code: string
  name: string
  description?: string | null
  difficulty_level: number
  learners?: string
  progress?: number
}

interface CourseCardProps {
  course: CourseCardData
}

export function CourseCard({ course }: CourseCardProps) {
  const config = getCourseConfig(course.code.toLowerCase())

  const footerItems: string[] = []
  if (course.learners) {
    footerItems.push(`${course.learners} 人正在学习`)
  }
  if (course.progress !== undefined) {
    footerItems.push(`${course.progress}%`)
  }
  if (footerItems.length === 0) {
    footerItems.push(`难度 ${course.difficulty_level}`)
  }

  return (
    <Link
      href={`/mastery/${course.id}`}
      className="group block bg-card border border-border hover:border-primary transition-colors"
    >
      {/* Top color bar */}
      <div className="h-2 bg-primary" />

      <div className="p-6">
        {/* Icon + name */}
        <div className="flex items-center gap-3 mb-3">
          <div
            className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
              config?.bgColor ?? 'bg-secondary'
            )}
          >
            <div className={cn('w-5 h-5', config?.color ?? 'text-primary')}>
              {config?.icon}
            </div>
          </div>
          <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
            {course.name}
          </h3>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
          {course.description || '暂无描述'}
        </p>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-border text-xs text-muted-foreground">
        {footerItems.join(' · ')}
      </div>
    </Link>
  )
}
