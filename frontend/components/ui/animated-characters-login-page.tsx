"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Mail, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react";
import { login } from "@/lib/api";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { validateEmail } from "@/lib/utils/validation";
import { CharacterGroup } from "@/components/ui/animated-characters";

function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isLookingAway, setIsLookingAway] = useState(false);
  const [isPasswordField, setIsPasswordField] = useState(false);
  const [lang, setLang] = useState<'en' | 'zh'>('zh');
  const [rememberMe, setRememberMe] = useState(false);

  // Field validation states
  const [emailTouched, setEmailTouched] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);

  const t = (en: string, zh: string) => lang === 'en' ? en : zh;

  // Password privacy - look away when typing in password field
  useEffect(() => {
    setIsLookingAway(isPasswordField);
  }, [isPasswordField]);

  // Real-time email validation
  useEffect(() => {
    if (emailTouched && email) {
      const result = validateEmail(email, lang);
      setEmailError(result.valid ? null : result.error || null);
    }
  }, [email, emailTouched, lang]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setEmailTouched(true);

    // Validate email
    const emailResult = validateEmail(email, lang);
    if (!emailResult.valid) {
      setError(emailResult.error || t("Invalid email", "邮箱格式错误"));
      return;
    }

    if (!password) {
      setError(t("Please enter password", "请输入密码"));
      return;
    }

    setIsLoading(true);

    try {
      await login(email, password, rememberMe);
      // Check if user is admin and redirect accordingly
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        if (user.is_admin) {
          router.push("/admin");
          return;
        }
      }
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("Invalid email or password", "邮箱或密码错误"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Content Section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground">
        <div className="relative z-20">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="size-8 rounded-lg bg-primary-foreground/10 backdrop-blur-sm flex items-center justify-center">
              <Sparkles className="size-4" />
            </div>
            <span>{t('DSA Platform', 'DSA 教学平台')}</span>
          </div>
        </div>

        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <CharacterGroup isLookingAway={isLookingAway} lang={lang} />
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-primary-foreground/60">
          <a href="#" className="hover:text-primary-foreground transition-colors">
            {t('Privacy Policy', '隐私政策')}
          </a>
          <a href="#" className="hover:text-primary-foreground transition-colors">
            {t('Terms of Service', '服务条款')}
          </a>
          <a href="#" className="hover:text-primary-foreground transition-colors">
            {t('Contact', '联系我们')}
          </a>
        </div>

        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      {/* Right Login Section */}
      <div className="flex items-center justify-center p-8 bg-background relative">
        {/* Language Switcher - Top Right Corner */}
        <div className="absolute top-6 right-6">
          <div className="inline-flex items-center bg-secondary rounded-full p-1">
            <button
              onClick={() => setLang('zh')}
              className={cn(
                "px-3 py-1 rounded-full text-[11px] font-medium transition-all",
                lang === 'zh'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              中文
            </button>
            <button
              onClick={() => setLang('en')}
              className={cn(
                "px-3 py-1 rounded-full text-[11px] font-medium transition-all",
                lang === 'en'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              EN
            </button>
          </div>
        </div>

        <div className="w-full max-w-[420px]">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
            <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span>{t('DSA Platform', 'DSA 教学平台')}</span>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold tracking-tight mb-2">{t('Welcome back!', '欢迎回来')}</h1>
            <p className="text-muted-foreground text-sm">{t('Please enter your details', '请输入您的账号信息')}</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg flex items-center gap-2">
                <AlertCircle className="size-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">{t('Email', '邮箱地址')}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder={t('you@example.com', 'you@example.com')}
                  value={email}
                  autoComplete="off"
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => { setIsTyping(false); setEmailTouched(true); }}
                  required
                  className={cn(
                    "h-12 pl-10 bg-background border-border/60 focus:border-primary",
                    emailTouched && emailError && "border-red-500 focus:border-red-500",
                    emailTouched && !emailError && email && "border-green-500 focus:border-green-500"
                  )}
                />
                {emailTouched && !emailError && email && (
                  <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-green-500" />
                )}
              </div>
              {emailTouched && emailError && (
                <p className="text-xs text-red-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" />
                  {emailError}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">{t('Password', '密码')}</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => { setIsTyping(true); setIsPasswordField(true); }}
                  onBlur={() => { setIsTyping(false); setIsPasswordField(false); }}
                  required
                  maxLength={100}
                  className="h-12 pr-10 bg-background border-border/60 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked === true)}
                />
                <Label
                  htmlFor="remember"
                  className="text-sm font-normal cursor-pointer"
                >
                  {t('Remember for 30 days', '记住我 30 天')}
                </Label>
              </div>
              <a
                href="/forgot-password"
                className="text-sm text-primary hover:underline font-medium"
              >
                {t('Forgot password?', '忘记密码？')}
              </a>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base font-medium"
              size="lg"
              disabled={isLoading}
            >
              {isLoading ? (t('Signing in...', '登录中...')) : (t('Log in', '登录'))}
            </Button>
          </form>

          {/* Sign Up Link */}
          <div className="text-center text-sm text-muted-foreground mt-8">
            {t("Don't have an account?", '没有账号？')}{" "}
            <a href="/register" className="text-foreground font-medium hover:underline">
              {t('Sign up', '立即注册')}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export const Component = LoginPage;
