interface LogoProps {
  className?: string
  size?: number
}

/**
 * 智码领航 Logo — 代码核心徽章
 *
 * 设计语言:
 * - 实心圆盘：完整的学习平台，稳定可信赖
 * - 白色括号 <>：编程/代码世界的入口
 * - 中心光点：AI 智能核心，聚焦与引领
 * - currentColor 自适应网站主色调
 */
export function Logo({ className, size = 40 }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* 实心圆盘底色 */}
      <circle cx="20" cy="20" r="18" fill="currentColor" />

      {/* 内圈高光（增加立体感） */}
      <circle
        cx="20"
        cy="20"
        r="18"
        fill="url(#logo-shine)"
        opacity="0.15"
      />

      {/* 左尖括号 < */}
      <path
        d="M16 14 L11 20 L16 26"
        fill="none"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.95"
      />

      {/* 右尖括号 > */}
      <path
        d="M24 14 L29 20 L24 26"
        fill="none"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.95"
      />

      {/* 中心 AI 核心光点 */}
      <circle cx="20" cy="20" r="3" fill="white" />

      {/* 渐变定义 */}
      <defs>
        <radialGradient
          id="logo-shine"
          cx="30%"
          cy="25%"
          r="60%"
        >
          <stop offset="0%" stopColor="white" stopOpacity="1" />
          <stop offset="100%" stopColor="white" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  )
}
