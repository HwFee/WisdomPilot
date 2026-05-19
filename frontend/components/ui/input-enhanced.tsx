/**
 * 增强的输入组件系统
 *
 * 包含：Input、Label、Textarea、Select、表单验证反馈
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { AlertCircle, CheckCircle, Eye, EyeOff } from "lucide-react"

// ── Input 组件 ──

const inputVariants = cva(
  `flex w-full rounded-xl border bg-background text-sm ring-offset-background
   transition-all duration-200
   file:border-0 file:bg-transparent file:text-sm file:font-medium
   placeholder:text-muted-foreground
   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
   disabled:cursor-not-allowed disabled:opacity-50`,
  {
    variants: {
      variant: {
        default: 'border-input',
        filled: 'border-transparent bg-muted',
        ghost: 'border-transparent bg-transparent hover:bg-muted/50',
      },
      inputSize: {
        sm: 'h-9 px-3 text-sm',
        default: 'h-10 px-4 text-sm',
        lg: 'h-12 px-4 text-base',
      },
      state: {
        default: '',
        error: 'border-red-500 focus-visible:ring-red-500',
        success: 'border-emerald-500 focus-visible:ring-emerald-500',
      },
    },
    defaultVariants: {
      variant: 'default',
      inputSize: 'default',
      state: 'default',
    },
  }
)

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  leftAddon?: React.ReactNode
  rightAddon?: React.ReactNode
  errorMessage?: string
  successMessage?: string
  hintMessage?: string
}

const Input = (
  {
    className,
    type,
    variant,
    inputSize,
    state,
    leftIcon,
    rightIcon,
    leftAddon,
    rightAddon,
    errorMessage,
    successMessage,
    hintMessage,
    ref,
    ...props
  }: InputProps & { ref?: React.Ref<HTMLInputElement> }
) => {
    const [showPassword, setShowPassword] = React.useState(false)
    const isPassword = type === 'password'
    const inputType = isPassword && showPassword ? 'text' : type

    // 自动检测状态
    const detectedState = errorMessage ? 'error' : successMessage ? 'success' : state

    return (
      <div className="w-full">
        <div className="relative flex items-stretch">
          {/* 左侧附加 */}
          {leftAddon && (
            <div className="flex items-center px-3 border border-r-0 border-input rounded-l-xl bg-muted text-muted-foreground text-sm">
              {leftAddon}
            </div>
          )}

          <div className="relative flex-1">
            {/* 左侧图标 */}
            {leftIcon && (
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
                {leftIcon}
              </div>
            )}

            <input
              type={inputType}
              className={cn(
                inputVariants({ variant, inputSize, state: detectedState }),
                leftIcon && 'pl-10',
                (rightIcon || isPassword) && 'pr-10',
                leftAddon && 'rounded-l-none',
                rightAddon && 'rounded-r-none',
                className
              )}
              ref={ref}
              {...props}
            />

            {/* 右侧图标或密码切换 */}
            {isPassword ? (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            ) : rightIcon ? (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
                {rightIcon}
              </div>
            ) : detectedState === 'error' ? (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none">
                <AlertCircle className="size-4" />
              </div>
            ) : detectedState === 'success' ? (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-500 pointer-events-none">
                <CheckCircle className="size-4" />
              </div>
            ) : null}
          </div>

          {/* 右侧附加 */}
          {rightAddon && (
            <div className="flex items-center px-3 border border-l-0 border-input rounded-r-xl bg-muted text-muted-foreground text-sm">
              {rightAddon}
            </div>
          )}
        </div>

        {/* 提示信息 */}
        {errorMessage && (
          <p className="mt-1.5 text-xs text-red-500 flex items-center gap-1">
            <AlertCircle className="size-3" />
            {errorMessage}
          </p>
        )}
        {successMessage && (
          <p className="mt-1.5 text-xs text-emerald-500 flex items-center gap-1">
            <CheckCircle className="size-3" />
            {successMessage}
          </p>
        )}
        {hintMessage && !errorMessage && !successMessage && (
          <p className="mt-1.5 text-xs text-muted-foreground">{hintMessage}</p>
        )}
      </div>
    )
  }
Input.displayName = "Input"

// ── Label 组件 ──

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean
  floating?: boolean
}

const Label = ({ className, children, required, floating, ref, ...props }: LabelProps & { ref?: React.Ref<HTMLLabelElement> }) => {
    return (
      <label
        ref={ref}
        className={cn(
          "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
          floating && "absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-all peer-focus:top-2 peer-focus:text-xs peer-focus:text-primary peer-[:not(:placeholder-shown)]:top-2 peer-[:not(:placeholder-shown)]:text-xs",
          className
        )}
        {...props}
      >
        {children}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
    )
  }
Label.displayName = "Label"

// ── Textarea 组件 ──

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  errorMessage?: string
  successMessage?: string
  hintMessage?: string
  showCount?: boolean
  maxLength?: number
  autoResize?: boolean
  minHeight?: number
  maxHeight?: number
}

const Textarea = ({
  className,
  errorMessage,
  successMessage,
  hintMessage,
  showCount,
  maxLength,
  autoResize,
  minHeight = 80,
  maxHeight = 300,
  value,
  onChange,
  ref,
  ...props
}: TextareaProps & { ref?: React.Ref<HTMLTextAreaElement> }) => {
    const textareaRef = React.useRef<HTMLTextAreaElement | null>(ref as any)
    const [charCount, setCharCount] = React.useState(0)

    // 自动调整高度
    React.useEffect(() => {
      if (autoResize && textareaRef.current) {
        textareaRef.current.style.height = 'auto'
        const scrollHeight = textareaRef.current.scrollHeight
        textareaRef.current.style.height = `${Math.min(Math.max(scrollHeight, minHeight), maxHeight)}px`
      }
    }, [value, autoResize, minHeight, maxHeight])

    // 字符计数
    React.useEffect(() => {
      if (showCount) {
        setCharCount(String(value || '').length)
      }
    }, [value, showCount])

    const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (maxLength && e.target.value.length > maxLength) {
        return
      }
      setCharCount(e.target.value.length)
      onChange?.(e)
    }

    const state = errorMessage ? 'error' : successMessage ? 'success' : 'default'

    return (
      <div className="w-full">
        <div className="relative">
          <textarea
            className={cn(
              `flex min-h-[80px] w-full rounded-xl border border-input bg-background px-4 py-3
               text-sm ring-offset-background placeholder:text-muted-foreground
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
               disabled:cursor-not-allowed disabled:opacity-50
               transition-all duration-200`,
              errorMessage && 'border-red-500 focus-visible:ring-red-500',
              successMessage && 'border-emerald-500 focus-visible:ring-emerald-500',
              className
            )}
            ref={textareaRef}
            value={value}
            onChange={handleTextareaChange}
            maxLength={maxLength}
            {...props}
          />

          {/* 字符计数 */}
          {!!showCount && (
            <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
              {charCount}{maxLength && ` / ${maxLength}`}
            </div>
          )}
        </div>

        {/* 提示信息 */}
        {errorMessage && (
          <p className="mt-1.5 text-xs text-red-500">{errorMessage}</p>
        )}
        {successMessage && (
          <p className="mt-1.5 text-xs text-emerald-500">{successMessage}</p>
        )}
        {hintMessage && !errorMessage && !successMessage && (
          <p className="mt-1.5 text-xs text-muted-foreground">{hintMessage}</p>
        )}
      </div>
    )
  }
Textarea.displayName = "Textarea"

// ── Select 组件 ──

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: Array<{ value: string; label: string; disabled?: boolean }>
  placeholder?: string
  errorMessage?: string
}

const Select = ({ className, options, placeholder, errorMessage, ref, ...props }: SelectProps & { ref?: React.Ref<HTMLSelectElement> }) => {
    return (
      <div className="w-full">
        <select
          className={cn(
            `flex h-10 w-full rounded-xl border bg-background px-4 py-2 text-sm ring-offset-background
             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
             disabled:cursor-not-allowed disabled:opacity-50
             transition-all duration-200`,
            errorMessage ? 'border-red-500' : 'border-input',
            className
          )}
          ref={ref}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>

        {errorMessage && (
          <p className="mt-1.5 text-xs text-red-500">{errorMessage}</p>
        )}
      </div>
    )
  }
Select.displayName = "Select"

// ── Checkbox 组件 ──

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string
  description?: string
}

const Checkbox = ({ className, label, description, ref, ...props }: CheckboxProps & { ref?: React.Ref<HTMLInputElement> }) => {
    return (
      <label className="flex items-start gap-3 cursor-pointer group">
        <input
          type="checkbox"
          className={cn(
            `size-4 mt-0.5 rounded border border-input bg-background
             checked:bg-primary checked:border-primary
             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
             disabled:cursor-not-allowed disabled:opacity-50
             transition-all duration-200`,
            className
          )}
          ref={ref}
          {...props}
        />
        <div className="flex flex-col">
          {label && (
            <span className="text-sm font-medium leading-none group-hover:text-primary transition-colors">
              {label}
            </span>
          )}
          {description && (
            <span className="text-xs text-muted-foreground mt-1">{description}</span>
          )}
        </div>
      </label>
    )
  }
Checkbox.displayName = "Checkbox"

// ── Radio 组件 ──

export interface RadioProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string
  description?: string
}

const Radio = ({ className, label, description, ref, ...props }: RadioProps & { ref?: React.Ref<HTMLInputElement> }) => {
    return (
      <label className="flex items-start gap-3 cursor-pointer group">
        <input
          type="radio"
          className={cn(
            `size-4 mt-0.5 border border-input bg-background rounded-full
             checked:border-primary checked:bg-primary
             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
             disabled:cursor-not-allowed disabled:opacity-50
             transition-all duration-200`,
            className
          )}
          ref={ref}
          {...props}
        />
        <div className="flex flex-col">
          {label && (
            <span className="text-sm font-medium leading-none group-hover:text-primary transition-colors">
              {label}
            </span>
          )}
          {description && (
            <span className="text-xs text-muted-foreground mt-1">{description}</span>
          )}
        </div>
      </label>
    )
  }
Radio.displayName = "Radio"

// ── FormField 包装组件 ──

interface FormFieldProps {
  label?: string
  required?: boolean
  hint?: string
  error?: string
  children: React.ReactNode
  className?: string
}

function FormField({ label, required, hint, error, children, className }: FormFieldProps) {
  return (
    <div className={cn("flex flex-col gap-y-2", className)}>
      {label && (
        <Label required={required}>
          {label}
        </Label>
      )}
      {children}
      {hint && !error && (
        <p className="text-xs text-muted-foreground">{hint}</p>
      )}
      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}
    </div>
  )
}

export {
  Input,
  Label,
  Textarea,
  Select,
  Checkbox,
  Radio,
  FormField,
  inputVariants,
}
