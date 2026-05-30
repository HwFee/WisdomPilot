/**
 * 图标系统统一导出
 *
 * 按功能域分类导出图标，便于统一管理和使用
 */

import {
  // 导航图标
  ArrowRight,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  ChevronLeft,
  Menu,
  X,
  ExternalLink,

  // 状态图标
  CheckCircle,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Info,
  Loader2,

  // 操作图标
  Play,
  Pause,
  RotateCcw,
  Save,
  Copy,
  Edit,
  Trash2,
  Download,
  Upload,
  Share,
  RefreshCw,

  // 学习功能图标
  BookOpen,
  GraduationCap,
  Brain,
  Lightbulb,
  FileText,
  Code,
  Terminal,

  // 挑战系统图标
  Trophy,
  Target,
  Swords,
  Medal,
  Crown,
  Star,
  Flame,
  Zap,

  // 社交功能图标
  Users,
  User,
  Heart,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,

  // 成就系统图标
  Award,
  Gem,
  Sparkles,
  Crown as CrownIcon,

  // 时间图标
  Clock,
  Calendar,
  Timer,
  History,

  // 文件图标
  File,
  FileCode,
  Folder,
  FolderOpen,

  // 设置图标
  Settings,
  Cog,
  Sliders,

  // 搜索图标
  Search,
  Filter,

  // 视图图标
  Eye,
  EyeOff,
  Maximize,
  Minimize,

  // 其他常用
  Plus,
  Minus,
  MoreHorizontal,
  MoreVertical,
  Home,
  LayoutDashboard,
  type LucideIcon,
} from 'lucide-react'

// ── 导航图标 ──
export const NavigationIcons = {
  ArrowRight,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  ChevronLeft,
  Menu,
  X,
  ExternalLink,
} as const

// ── 状态图标 ──
export const StatusIcons = {
  CheckCircle,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Info,
  Loader2,
} as const

// ── 操作图标 ──
export const ActionIcons = {
  Play,
  Pause,
  RotateCcw,
  Save,
  Copy,
  Edit,
  Trash2,
  Download,
  Upload,
  Share,
  RefreshCw,
} as const

// ── 学习功能图标 ──
export const LearningIcons = {
  BookOpen,
  GraduationCap,
  Brain,
  Lightbulb,
  FileText,
  Code,
  Terminal,
} as const

// ── 挑战系统图标 ──
export const ChallengeIcons = {
  Trophy,
  Target,
  Swords,
  Medal,
  Crown,
  Star,
  Flame,
  Zap,
} as const

// ── 社交功能图标 ──
export const SocialIcons = {
  Users,
  User,
  Heart,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
} as const

// ── 成就系统图标 ──
export const AchievementIcons = {
  Award,
  Gem,
  Sparkles,
  Crown: CrownIcon,
} as const

// ── 时间图标 ──
export const TimeIcons = {
  Clock,
  Calendar,
  Timer,
  History,
} as const

// ── 文件图标 ──
export const FileIcons = {
  File,
  FileCode,
  Folder,
  FolderOpen,
} as const

// ── 设置图标 ──
export const SettingsIcons = {
  Settings,
  Cog,
  Sliders,
} as const

// ── 搜索图标 ──
export const SearchIcons = {
  Search,
  Filter,
} as const

// ── 视图图标 ──
export const ViewIcons = {
  Eye,
  EyeOff,
  Maximize,
  Minimize,
} as const

// ── 其他常用图标 ──
export const CommonIcons = {
  Plus,
  Minus,
  MoreHorizontal,
  MoreVertical,
  Home,
  LayoutDashboard,
} as const

// 导出类型
export type { LucideIcon }
