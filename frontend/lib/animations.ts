/**
 * 动画工具库
 *
 * 提供统一的动画变体、hooks和工具函数
 */

import { useState, useEffect, useRef, useCallback, useSyncExternalStore } from 'react'
import type { Variants, Transition } from 'framer-motion'

// ── 标准动画变体 ──

/** 淡入淡出 */
export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

/** 从下方滑入 */
export const slideUp: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
}

/** 从上方滑入 */
const slideDown: Variants = {
  initial: { opacity: 0, y: -20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
}

/** 从右侧滑入 */
const slideInFromRight: Variants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
}

/** 从左侧滑入 */
const slideInFromLeft: Variants = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
}

/** 缩放淡入 */
export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
}

/** 缩放弹出 */
const popIn: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 20,
    },
  },
  exit: { opacity: 0, scale: 0.8 },
}

/** 弹跳效果 */
const bounce: Variants = {
  initial: { scale: 0.3, opacity: 0 },
  animate: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 20,
    },
  },
}

/** 无动画（仅可见性） */
const visible: Variants = {
  initial: { opacity: 1 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

// ── 交错动画 ──

/** 交错容器 */
export const staggerContainer: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.05,
    },
  },
}

/** 交错子项 */
export const staggerItem: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
}

/** 快速交错 */
const staggerContainerFast: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.02,
    },
  },
}

/** 慢速交错 */
const staggerContainerSlow: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
}

// ── 默认过渡配置 ──

const defaultTransition: Transition = {
  duration: 0.3,
  ease: [0.4, 0, 0.2, 1],
}

const springTransition: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 20,
}

const slowTransition: Transition = {
  duration: 0.5,
  ease: [0.4, 0, 0.2, 1],
}

// ── 动画 Hooks ──

/**
 * 数字计数动画
 */
function useCountUp(
  end: number,
  duration: number = 1000,
  start: number = 0,
  decimals: number = 0
) {
  const [count, setCount] = useState(start)

  useEffect(() => {
    let startTime: number | null = null
    let animationFrame: number

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)

      // 缓动函数
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const current = start + (end - start) * easeOutQuart

      setCount(Number(current.toFixed(decimals)))

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate)
      }
    }

    animationFrame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationFrame)
  }, [end, duration, start, decimals])

  return count
}

/**
 * 滚动触发动画
 */
function useScrollAnimation(threshold: number = 0.1) {
  const [isVisible, setIsVisible] = useState(false)
  const observerRef = useRef<IntersectionObserver | null>(null)
  const thresholdRef = useRef(threshold)

  useEffect(() => {
    thresholdRef.current = threshold
  }, [threshold])

  const setRef = useCallback(
    (element: HTMLElement | null) => {
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = null
      }
      if (element && !isVisible) {
        observerRef.current = new IntersectionObserver(
          ([entry]) => {
            if (entry.isIntersecting) {
              setIsVisible(true)
              observerRef.current?.disconnect()
            }
          },
          { threshold: thresholdRef.current }
        )
        observerRef.current.observe(element)
      }
    },
    [isVisible]
  )

  return { ref: setRef, isVisible }
}

/**
 * 悬停动画状态
 */
const HOVER_VARIANTS = {
  rest: { scale: 1 },
  hover: { scale: 1.02 },
}

function useHoverAnimation() {
  const [isHovered, setIsHovered] = useState(false)

  const hoverProps = {
    onMouseEnter: () => setIsHovered(true),
    onMouseLeave: () => setIsHovered(false),
  }

  return {
    isHovered,
    hoverProps,
    hoverVariants: HOVER_VARIANTS,
    animate: isHovered ? 'hover' : 'rest',
  }
}

/**
 * 点击动画状态
 */
const TAP_VARIANTS = {
  untapped: { scale: 1 },
  tapped: { scale: 0.98 },
}

function useTapAnimation() {
  const [isTapped, setIsTapped] = useState(false)

  const tapProps = {
    onMouseDown: () => setIsTapped(true),
    onMouseUp: () => setIsTapped(false),
    onMouseLeave: () => setIsTapped(false),
  }

  return {
    isTapped,
    tapProps,
    tapVariants: TAP_VARIANTS,
    animate: isTapped ? 'tapped' : 'untapped',
  }
}

/**
 * 打字机效果
 */
function useTypewriter(text: string, speed: number = 50) {
  const [state, setState] = useState<{ text: string; complete: boolean }>({ text: '', complete: false })

  // react-doctor-disable-next-line no-cascading-set-state, react-doctor/no-cascading-set-state
  useEffect(() => {
    let index = 0
    let timer: ReturnType<typeof setTimeout> | null = null
    const tick = () => {
      if (index < text.length) {
        setState({ text: text.slice(0, index + 1), complete: false })
        index++
        timer = setTimeout(tick, speed)
      } else {
        setState({ text, complete: true })
      }
    }
    timer = setTimeout(tick, speed)
    return () => { if (timer) clearTimeout(timer) }
  }, [text, speed])

  return { displayText: state.text, isComplete: state.complete }
}

/**
 * 延迟动画
 */
function useDelayedAnimation(delay: number = 300) {
  const [shouldAnimate, setShouldAnimate] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShouldAnimate(true)
    }, delay)

    return () => clearTimeout(timer)
  }, [delay])

  return shouldAnimate
}

/**
 * 视差滚动
 */
function useParallax(speed: number = 0.5) {
  const [offset, setOffset] = useState(0)
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const handleScroll = () => {
      if (!ref.current) return
      const rect = ref.current.getBoundingClientRect()
      const scrolled = window.scrollY
      const elementTop = rect.top + scrolled
      const parallaxOffset = (scrolled - elementTop) * speed
      setOffset(parallaxOffset)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [speed])

  return { ref, offset }
}

// ── 工具函数 ──

/**
 * 创建延迟过渡
 */
function createDelayedTransition(delay: number): Transition {
  return {
    ...defaultTransition,
    delay,
  }
}

/**
 * 创建交错延迟
 */
function createStaggerDelays(count: number, baseDelay: number = 0.05): number[] {
  return Array.from({ length: count }, (_, i) => i * baseDelay)
}

/**
 * 减少动画偏好检测
 */
function subscribePrefersReducedMotion(callback: () => void) {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', callback)
  return () => mediaQuery.removeEventListener('change', callback)
}

function getPrefersReducedMotionSnapshot() {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function getPrefersReducedMotionServerSnapshot() {
  return false
}

function usePrefersReducedMotion() {
  return useSyncExternalStore(
    subscribePrefersReducedMotion,
    getPrefersReducedMotionSnapshot,
    getPrefersReducedMotionServerSnapshot,
  )
}

/**
 * 获取动画变体（考虑减少动画偏好）
 */
function getAnimationVariant(
  variant: Variants,
  prefersReducedMotion: boolean
): Variants {
  if (prefersReducedMotion) {
    return visible
  }
  return variant
}
