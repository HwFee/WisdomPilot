"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button-enhanced";
import { Input } from "@/components/ui/input-enhanced";
import { Label } from "@/components/ui/input-enhanced";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, User, Sparkles, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { login } from "@/lib/api";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { CharacterGroup } from "@/components/ui/animated-characters";
import { fadeIn, slideUp } from "@/lib/animations";

function LoginPage() {
  const { push } = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isLookingAway, setIsLookingAway] = useState(false);
  const [isPasswordField, setIsPasswordField] = useState(false);
  const [lang, setLang] = useState<'en' | 'zh'>('zh');
  const [rememberMe, setRememberMe] = useState(false);

  // Field validation states
  const [usernameTouched, setUsernameTouched] = useState(false);

  const t = (en: string, zh: string) => lang === 'en' ? en : zh;

  // Password privacy - look away when typing in password field
  useEffect(() => {
    setIsLookingAway(isPasswordField);
  }, [isPasswordField]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setUsernameTouched(true);

    if (!username.trim()) {
      setError(t("Please enter username", "请输入用户名"));
      return;
    }

    if (!password) {
      setError(t("Please enter password", "请输入密码"));
      return;
    }

    setIsLoading(true);

    try {
      await login(username.trim(), password, rememberMe);
      // Check if user is admin and redirect accordingly
      const storedUser = localStorage.getItem('user:v1');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        if (user.is_admin) {
          push("/admin");
          return;
        }
      }
      push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("Invalid username or password", "用户名或密码错误"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Content Section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground overflow-hidden">
        {/* 动态背景网格 */}
        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />

        {/* 渐变装饰球 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl"
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl"
        />

        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative z-20"
        >
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="size-8 rounded-lg bg-primary-foreground/10 backdrop-blur-sm flex items-center justify-center">
              <Sparkles className="size-4" />
            </div>
            <span>{t('ZhiMa LingHang', '智码领航')}</span>
          </div>
        </motion.div>

        {/* 动画角色 */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="relative z-20 flex items-end justify-center h-[500px]"
        >
          <CharacterGroup isLookingAway={isLookingAway} lang={lang} />
        </motion.div>

        {/* 底部链接 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="relative z-20 flex items-center gap-8 text-sm text-primary-foreground/60"
        >
          <a href="#" className="hover:text-primary-foreground transition-colors">
            {t('Privacy Policy', '隐私政策')}
          </a>
          <a href="#" className="hover:text-primary-foreground transition-colors">
            {t('Terms of Service', '服务条款')}
          </a>
          <a href="#" className="hover:text-primary-foreground transition-colors">
            {t('Contact', '联系我们')}
          </a>
        </motion.div>
      </div>

      {/* Right Login Section */}
      <div className="flex items-center justify-center p-8 bg-background relative overflow-hidden">
        {/* 背景装饰 */}
        <div className="absolute inset-0 gradient-mesh opacity-50" />

        {/* 语言切换器 */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="absolute top-6 right-6 z-10"
        >
          <div className="inline-flex items-center bg-secondary/80 backdrop-blur-sm rounded-full p-1 border border-border/50">
            <button type="button"
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
            <button type="button"
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
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-[420px] relative z-10"
        >
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
            <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span>{t('ZhiMa LingHang', '智码领航')}</span>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-3xl font-bold tracking-tight mb-2"
            >
              {t('Welcome back!', '欢迎回来')}
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="text-muted-foreground text-sm"
            >
              {t('Please enter your details', '请输入您的账号信息')}
            </motion.p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="gap-y-5">
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-xl flex items-center gap-2"
              >
                <AlertCircle className="size-4 flex-shrink-0" />
                {error}
              </motion.div>
            )}

            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
              className="gap-y-2"
            >
              <Label htmlFor="username" required>{t('Username', '用户名')}</Label>
              <Input
                id="username"
                type="text"
                placeholder={t('Enter your username', '请输入用户名')}
                value={username}
                autoComplete="username"
                leftIcon={<User className="size-4" />}
                onChange={(e) => setUsername(e.target.value)}
                onFocus={() => setIsTyping(true)}
                onBlur={() => { setIsTyping(false); setUsernameTouched(true); }}
                inputSize="lg"
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.4 }}
              className="gap-y-2"
            >
              <Label htmlFor="password" required>{t('Password', '密码')}</Label>
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => { setIsTyping(true); setIsPasswordField(true); }}
                onBlur={() => { setIsTyping(false); setIsPasswordField(false); }}
                maxLength={100}
                inputSize="lg"
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.5 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-x-2">
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
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.6 }}
            >
              <Button
                type="submit"
                variant="gradient"
                size="lg"
                fullWidth
                loading={isLoading}
                rightIcon={!isLoading && <ArrowRight className="size-4" />}
              >
                {isLoading ? (t('Signing in...', '登录中...')) : (t('Log in', '登录'))}
              </Button>
            </motion.div>
          </form>

          {/* Sign Up Link */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.7 }}
            className="text-center text-sm text-muted-foreground mt-8"
          >
            {t("Don't have an account?", '没有账号？')}{" "}
            <a href="/register" className="text-foreground font-medium hover:underline">
              {t('Sign up', '立即注册')}
            </a>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export const Component = LoginPage;
