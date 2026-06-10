import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { getCourseConfig } from '@/lib/icons/course-icons'
import type { CourseSummary } from '@/types/api'

interface CourseCardProps {
  course: CourseSummary
}

function DifficultyDots({ level }: { level: number }) {
  return (
    <div className="flex gap-1 mt-1">
      {Array.from({ length: 4 }, (_, i) => (
        <div
          key={i}
          className={`size-1.5 rounded-full ${i < level ? 'bg-primary' : 'bg-muted'}`}
        />
      ))}
    </div>
  )
}

export function CourseCard({ course }: CourseCardProps) {
  const config = getCourseConfig(course.code.toLowerCase())
  const gradient = config?.gradient || 'from-primary to-primary-600'

  return (
    <Link
      href={`/mastery/${course.id}`}
      className="group relative p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all card-interactive overflow-hidden"
    >
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${gradient}`} />

      <div className="flex items-center gap-4 mb-4 mt-2">
        <div className={`size-14 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform`}>
          <div className="size-7 text-white">{config?.icon}</div>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
            {course.name}
          </h3>
          <DifficultyDots level={course.difficulty_level} />
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
        {course.description || '暂无描述'}
      </p>

      <div className="flex items-center justify-between text-xs pt-3 border-t border-border/50">
        <span className="text-muted-foreground">
          难度 {'★'.repeat(course.difficulty_level)}
        </span>
        <span className="flex items-center gap-1 text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
          开始学习
          <ChevronRight className="size-3" />
        </span>
      </div>
    </Link>
  )
}
