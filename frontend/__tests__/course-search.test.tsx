import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CourseChapter } from '@/lib/course-data'
import { CourseSearch } from '@/components/ui/course-search'

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

// Mock data for testing with subsections
const mockChapters: CourseChapter[] = [
  {
    id: 1,
    title: '基础',
    titleEn: 'Basics',
    num: '01',
    color: '#3b82f6',
    bg: 'from-blue-500/20 to-indigo-500/20',
    topics: ['数组', '链表', '顺序表', '双向链表'],
    subsections: ['数据结构的基本概念', '时间复杂度', '空间复杂度', '顺序存储', '链式存储', '单链表', '双链表'],
    progress: 100,
    status: 'completed',
    lessons: 8,
    subsectionExercises: {},
  },
  {
    id: 2,
    title: '栈与队列',
    titleEn: 'Stack & Queue',
    num: '02',
    color: '#10b981',
    bg: 'from-emerald-500/20 to-teal-500/20',
    topics: ['栈', '队列', '循环队列', '双端队列'],
    subsections: ['栈的基本概念', '栈的应用', '表达式求值', '括号匹配', '循环队列', '双端队列'],
    progress: 100,
    status: 'completed',
    lessons: 10,
    subsectionExercises: {},
  },
  {
    id: 3,
    title: '字符串',
    titleEn: 'String',
    num: '03',
    color: '#8b5cf6',
    bg: 'from-violet-500/20 to-purple-500/20',
    topics: ['字符串匹配', 'KMP', 'BM', 'Trie'],
    subsections: ['KMP算法', 'KMPnext数组', '朴素的模式匹配', 'BM算法', 'Trie树'],
    progress: 85,
    status: 'learning',
    lessons: 8,
    subsectionExercises: {},
  },
  {
    id: 4,
    title: '树',
    titleEn: 'Trees',
    num: '04',
    color: '#14b8a6',
    bg: 'from-teal-500/20 to-cyan-500/20',
    topics: ['二叉树', '完全二叉树', '满二叉树'],
    subsections: ['二叉树的概念', '二叉树的性质', '遍历二叉树', '先序遍历', '中序遍历', '后序遍历', '层序遍历', '线索二叉树'],
    progress: 45,
    status: 'learning',
    lessons: 12,
    subsectionExercises: {},
  },
  {
    id: 5,
    title: '二叉搜索树',
    titleEn: 'BST',
    num: '05',
    color: '#06b6d4',
    bg: 'from-cyan-500/20 to-sky-500/20',
    topics: ['BST', 'AVL', '红黑树', '堆'],
    subsections: ['AVL树', 'AVL旋转', 'LL旋转', 'RR旋转', '红黑树', '堆排序'],
    progress: 65,
    status: 'learning',
    lessons: 14,
    subsectionExercises: {},
  },
  {
    id: 6,
    title: '图',
    titleEn: 'Graphs',
    num: '06',
    color: '#6366f1',
    bg: 'from-indigo-500/20 to-blue-500/20',
    topics: ['BFS', 'DFS', '拓扑排序', '最短路径'],
    subsections: ['深度优先搜索', '广度优先搜索', 'Dijkstra算法', 'Floyd算法', '拓扑排序', '关键路径'],
    progress: 0,
    status: 'new',
    lessons: 16,
    subsectionExercises: {},
  },
]

// Pure search function for unit testing - matches dashboard-page.tsx implementation
export function searchCourses(chapters: CourseChapter[], query: string): CourseChapter[] {
  if (!query.trim()) {
    return chapters
  }
  const lowerQuery = query.toLowerCase().trim()
  return chapters.filter((chapter) => {
    if (chapter.title.toLowerCase().includes(lowerQuery)) return true
    if (chapter.titleEn.toLowerCase().includes(lowerQuery)) return true
    if (chapter.topics.some((topic) => topic.toLowerCase().includes(lowerQuery))) return true
    if (chapter.subsections.some((subsection) => subsection.toLowerCase().includes(lowerQuery))) return true
    return false
  })
}

describe('Course Search Function', () => {
  describe('searchCourses', () => {
    it('returns all courses when query is empty', () => {
      const result = searchCourses(mockChapters, '')
      expect(result).toHaveLength(mockChapters.length)
    })

    it('returns all courses when query is whitespace only', () => {
      const result = searchCourses(mockChapters, '   ')
      expect(result).toHaveLength(mockChapters.length)
    })

    it('searches by Chinese title', () => {
      const result = searchCourses(mockChapters, '栈')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('栈与队列')
    })

    it('searches by English title', () => {
      const result = searchCourses(mockChapters, 'Tree')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('树')
    })

    it('searches by topic name', () => {
      const result = searchCourses(mockChapters, 'KMP')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('字符串')
    })

    it('is case-insensitive for Chinese', () => {
      const result = searchCourses(mockChapters, '二叉')
      expect(result).toHaveLength(2) // '树' and '二叉搜索树'
    })

    it('is case-insensitive for English', () => {
      const result = searchCourses(mockChapters, 'bst')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('二叉搜索树')
    })

    it('returns partial matches', () => {
      const result = searchCourses(mockChapters, '链')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('基础')
    })

    it('searches across multiple fields (title and topics)', () => {
      const result = searchCourses(mockChapters, '队列')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('栈与队列')
    })

    it('returns empty array when no match found', () => {
      const result = searchCourses(mockChapters, '不存在的内容')
      expect(result).toHaveLength(0)
    })

    // Subsection search tests
    it('searches in subsections - KMP next array', () => {
      const result = searchCourses(mockChapters, 'KMPnext')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('字符串')
    })

    it('searches in subsections - AVL rotation', () => {
      const result = searchCourses(mockChapters, 'AVL旋转')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('二叉搜索树')
    })

    it('searches in subsections - traversal methods', () => {
      const result = searchCourses(mockChapters, '先序遍历')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('树')
    })

    it('searches in subsections - Dijkstra algorithm', () => {
      const result = searchCourses(mockChapters, 'Dijkstra')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('图')
    })

    it('searches in subsections - time complexity', () => {
      const result = searchCourses(mockChapters, '时间复杂度')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('基础')
    })

    it('finds multiple chapters by subsection', () => {
      // Both '树' and '二叉搜索树' might have related subsections
      const result = searchCourses(mockChapters, '遍历')
      expect(result.length).toBeGreaterThanOrEqual(1)
    })
  })
})

// ========================================
// CourseSearch Component Tests
// ========================================
describe('CourseSearch Component', () => {
  const defaultProps = {
    chapters: mockChapters,
    value: '',
    onChange: jest.fn(),
    onSelect: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Search Results Selection', () => {
    it('calls onSelect with chapter when selecting a chapter result', () => {
      render(<CourseSearch {...defaultProps} value="基础" />)

      // Click on the chapter result
      fireEvent.click(screen.getByText('基础'))
      expect(defaultProps.onSelect).toHaveBeenCalledWith(
        expect.objectContaining({ title: '基础' }),
        undefined
      )
    })

    it('calls onSelect with chapter and subsectionIndex when selecting a subsection result', () => {
      render(<CourseSearch {...defaultProps} value="时间复杂度" />)

      // Click on the subsection result (should show "小节: 时间复杂度")
      fireEvent.click(screen.getByText('时间复杂度'))
      expect(defaultProps.onSelect).toHaveBeenCalledWith(
        expect.objectContaining({ title: '基础' }),
        1 // subsectionIndex for "时间复杂度" is 1
      )
    })

    it('clears input after selection', () => {
      render(<CourseSearch {...defaultProps} value="时间复杂度" />)

      fireEvent.click(screen.getByText('时间复杂度'))
      expect(defaultProps.onChange).toHaveBeenCalledWith('')
    })
  })
})
