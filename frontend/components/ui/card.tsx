import * as React from "react"
import Image from "next/image"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Card 组件系统
 *
 * 特性：
 * - 多种变体：default、interactive、glass、flat、gradient、elevated
 * - 不同内边距：none、sm、default、lg、xl
 * - 子组件：CardHeader、CardTitle、CardDescription、CardContent、CardFooter
 * - 悬停交互效果
 */

const cardVariants = cva(
  'rounded-2xl transition-all duration-300',
  {
    variants: {
      variant: {
        default: 'bg-card border border-border',
        interactive: `
          bg-card border border-border
          hover:border-primary/30 hover:shadow-xl hover:-translate-y-1
          cursor-pointer
        `,
        glass: 'glass border border-white/10',
        flat: 'bg-muted/50 border-none',
        gradient: `
          bg-gradient-to-br from-card to-muted/50
          border border-border
        `,
        elevated: `
          bg-card border border-border
          shadow-lg hover:shadow-xl
        `,
      },
      padding: {
        none: '',
        sm: 'p-3',
        default: 'p-4',
        lg: 'p-6',
        xl: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'default',
    },
  }
)

interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  asChild?: boolean
  ref?: React.Ref<HTMLDivElement>
}

const Card = ({ className, variant, padding, ref, ...props }: CardProps) => (
  <div
    ref={ref}
    className={cn(cardVariants({ variant, padding, className }))}
    {...props}
  />
)
Card.displayName = "Card"

// CardHeader - 卡片头部
const CardHeader = ({ className, ref, ...props }: React.HTMLAttributes<HTMLDivElement> & { ref?: React.Ref<HTMLDivElement> }) => (
  <div
    ref={ref}
    className={cn("flex flex-col gap-y-1.5 pb-4", className)}
    {...props}
  />
)
CardHeader.displayName = "CardHeader"

// CardTitle - 卡片标题
const CardTitle = ({ className, ref, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { ref?: React.Ref<HTMLParagraphElement> }) => (
  // eslint-disable-next-line jsx-a11y/heading-has-content
  <h3
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
)
CardTitle.displayName = "CardTitle"

// CardDescription - 卡片描述
const CardDescription = ({ className, ref, ...props }: React.HTMLAttributes<HTMLParagraphElement> & { ref?: React.Ref<HTMLParagraphElement> }) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
)
CardDescription.displayName = "CardDescription"

// CardContent - 卡片内容
const CardContent = ({ className, ref, ...props }: React.HTMLAttributes<HTMLDivElement> & { ref?: React.Ref<HTMLDivElement> }) => (
  <div ref={ref} className={cn("", className)} {...props} />
)
CardContent.displayName = "CardContent"

// CardFooter - 卡片底部
const CardFooter = ({ className, ref, ...props }: React.HTMLAttributes<HTMLDivElement> & { ref?: React.Ref<HTMLDivElement> }) => (
  <div
    ref={ref}
    className={cn("flex items-center pt-4", className)}
    {...props}
  />
)
CardFooter.displayName = "CardFooter"

// CardImage - 卡片图片（可选）
const CardImage = ({ className, src, alt, aspectRatio = 'video', ref, ...props }: React.HTMLAttributes<HTMLDivElement> & {
  src: string
  alt: string
  aspectRatio?: 'video' | 'square' | 'portrait'
  ref?: React.Ref<HTMLDivElement>
}) => {
  const aspectClasses = {
    video: 'aspect-video',
    square: 'aspect-square',
    portrait: 'aspect-[3/4]',
  }

  return (
    <div
      ref={ref}
      className={cn("overflow-hidden rounded-t-2xl relative", aspectClasses[aspectRatio], className)}
      {...props}
    >
      <Image
        src={src}
        alt={alt}
        fill
        className="object-cover transition-transform duration-300 group-hover:scale-105"
        sizes="(max-width: 768px) 100vw, 50vw"
      />
    </div>
  )
}
CardImage.displayName = "CardImage"

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardImage,
  cardVariants,
}
