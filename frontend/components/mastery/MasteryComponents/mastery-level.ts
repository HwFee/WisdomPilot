/**
 * 掌握度等级 → 视觉样式 / 文案 映射。
 *
 * 该模块是纯数据 + 工具函数（无 React 依赖），可以从组件文件中
 * 安全地解耦出来，让组件文件只导出组件，让 Fast Refresh 能正确
 * 保留组件状态。
 */

export interface MasteryLevelInfo {
  /** 中文标签：精通 / 熟练 / 练习 / 学习 / 入门 */
  label: string
  /** 徽章背景色（含 dark 变体） */
  badgeColor: string
  /** 文字色 */
  textColor: string
  /** 进度条填充色 */
  progressColor: string
}

export function getMasteryLevel(score: number): MasteryLevelInfo {
  if (score >= 95) {
    return {
      label: '精通',
      badgeColor: 'bg-success/10 dark:bg-success/20',
      textColor: 'text-success',
      progressColor: 'bg-success',
    }
  } else if (score >= 85) {
    return {
      label: '熟练',
      badgeColor: 'bg-primary/10 dark:bg-primary/20',
      textColor: 'text-primary',
      progressColor: 'bg-primary',
    }
  } else if (score >= 70) {
    return {
      label: '练习',
      badgeColor: 'bg-warning/10 dark:bg-warning/20',
      textColor: 'text-warning',
      progressColor: 'bg-warning',
    }
  } else if (score >= 50) {
    return {
      label: '学习',
      badgeColor: 'bg-warning/10 dark:bg-warning/20',
      textColor: 'text-warning',
      progressColor: 'bg-warning/80',
    }
  } else {
    return {
      label: '入门',
      badgeColor: 'bg-muted',
      textColor: 'text-muted-foreground',
      progressColor: 'bg-muted-foreground/40',
    }
  }
}
