"use client";

import Link from 'next/link'
import { useState, useEffect, useRef, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Mail, Sparkles, User, AlertCircle, CheckCircle2 } from "lucide-react";
import { register } from "@/lib/api";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  validateEmail,
  validateUsername,
  validatePassword,
  validatePasswordConfirm,
} from "@/lib/utils/validation";
import { PasswordStrengthIndicator } from "./password-strength-indicator";
import { CharacterGroup } from "@/components/ui/animated-characters";

function RegisterPage() {
  const { push } = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();
  const isTypingRef = useRef(false);
  const isPasswordFieldRef = useRef(false);
  const [isLookingAway, setIsLookingAway] = useState(false);
  const [lang, setLang] = useState<'en' | 'zh'>('zh');
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  // Field validation states
  const [emailTouched, setEmailTouched] = useState(false);
  const [usernameTouched, setUsernameTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmPasswordTouched, setConfirmPasswordTouched] = useState(false);

  // Validation results
  const [emailError, setEmailError] = useState<string | null>(null);
  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [passwordResult, setPasswordResult] = useState<ReturnType<typeof validatePassword> | null>(null);
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | null>(null);

  const t = (en: string, zh: string) => lang === 'en' ? en : zh;



  // Real-time validation
  useEffect(() => {
    if (emailTouched && email) {
      const result = validateEmail(email, lang);
      setEmailError(result.valid ? null : result.error || null);
    }
  }, [email, emailTouched, lang]);

  useEffect(() => {
    if (usernameTouched && username) {
      const result = validateUsername(username, lang);
      setUsernameError(result.valid ? null : result.error || null);
    }
  }, [username, usernameTouched, lang]);

  useEffect(() => {
    if (passwordTouched && password) {
      const result = validatePassword(password, lang);
      setPasswordResult(result);
    } else {
      setPasswordResult(null);
    }
  }, [password, passwordTouched, lang]);

  useEffect(() => {
    if (confirmPasswordTouched && confirmPassword) {
      const result = validatePasswordConfirm(password, confirmPassword, lang);
      setConfirmPasswordError(result.valid ? null : result.error || null);
    }
  }, [password, confirmPassword, confirmPasswordTouched, lang]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Mark all fields as touched to show validation errors
    setEmailTouched(true);
    setUsernameTouched(true);
    setPasswordTouched(true);
    setConfirmPasswordTouched(true);

    // Validate all fields
    const emailResult = validateEmail(email, lang);
    const usernameResult = validateUsername(username, lang);
    const passwordRes = validatePassword(password, lang);
    const confirmResult = validatePasswordConfirm(password, confirmPassword, lang);

    if (!emailResult.valid) {
      setError(emailResult.error || t("Invalid email", "邮箱格式错误"));
      return;
    }

    if (!usernameResult.valid) {
      setError(usernameResult.error || t("Invalid username", "用户名格式错误"));
      return;
    }

    if (!passwordRes.valid) {
      setError(passwordRes.error || t("Invalid password", "密码格式错误"));
      return;
    }

    if (!confirmResult.valid) {
      setError(confirmResult.error || t("Passwords do not match", "两次密码输入不一致"));
      return;
    }

    if (!agreedToTerms) {
      setError(t("Please agree to the Terms of Service and Privacy Policy", "请同意服务条款和隐私政策"));
      return;
    }

    startTransition(async () => {
      try {
        await register(email, username, password);
        push("/login");
      } catch (err) {
        setError(err instanceof Error ? err.message : t("Registration failed. Please try again.", "注册失败，请重试。"));
      }
    });
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
            <span>{t('ZhiMa LingHang', '智码领航')}</span>
          </div>
        </div>

        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <CharacterGroup isLookingAway={isLookingAway} lang={lang} />
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-primary-foreground/60">
          <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
            {t('Privacy Policy', '隐私政策')}
          </button>
          <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
            {t('Terms of Service', '服务条款')}
          </button>
          <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
            {t('Contact', '联系我们')}
          </button>
        </div>

        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      {/* Right Register Section */}
      <div className="flex items-center justify-center p-8 bg-background relative">
        {/* Language Switcher - Top Right Corner */}
        <div className="absolute top-6 right-6">
          <div className="inline-flex items-center bg-secondary rounded-full p-1">
            <button type="button"
              onClick={() => setLang('zh')}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${
                lang === 'zh'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              中文
            </button>
            <button type="button"
              onClick={() => setLang('en')}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${
                lang === 'en'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
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
            <span>{t('ZhiMa LingHang', '智码领航')}</span>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-semibold tracking-tight mb-2">{t('Create your account', '创建账号')}</h1>
            <p className="text-muted-foreground text-sm">{t('Join our learning platform', '加入我们的学习平台')}</p>
          </div>

          {/* Register Form */}
          <form onSubmit={handleSubmit} className="gap-y-4">
            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
                {error}
              </div>
            )}

            <div className="gap-y-2">
              <Label htmlFor="username" className="text-sm font-medium">{t('Username', '用户名')}</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="username"
                  type="text"
                  placeholder={t('yourname', 'username')}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => { isTypingRef.current = true; }}
                  onBlur={() => { isTypingRef.current = false; setUsernameTouched(true); }}
                  className={cn(
                    "h-12 pl-10 bg-background border-border/60 focus:border-primary",
                    usernameTouched && usernameError && "border-red-500 focus:border-red-500",
                    usernameTouched && !usernameError && username && "border-green-500 focus:border-green-500"
                  )}
                />
                {usernameTouched && !usernameError && username && (
                  <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-green-500" />
                )}
              </div>
              {usernameTouched && usernameError && (
                <p className="text-xs text-red-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" />
                  {usernameError}
                </p>
              )}
            </div>

            <div className="gap-y-2">
              <Label htmlFor="email" className="text-sm font-medium">{t('Email', '邮箱地址')}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder={t('you@example.com', 'you@example.com')}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => { isTypingRef.current = true; }}
                  onBlur={() => { isTypingRef.current = false; setEmailTouched(true); }}
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

            <div className="gap-y-2">
              <Label htmlFor="password" className="text-sm font-medium">{t('Password', '密码')}</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder={t('Min. 8 characters', '至少8个字符')}
                  value={password}
                  maxLength={100}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => { isTypingRef.current = true; isPasswordFieldRef.current = true; setIsLookingAway(true); setPasswordTouched(true); }}
                  onBlur={() => { isTypingRef.current = false; isPasswordFieldRef.current = false; setIsLookingAway(false); }}
                  className={cn(
                    "h-12 pr-10 bg-background border-border/60 focus:border-primary",
                    passwordTouched && passwordResult && !passwordResult.valid && "border-red-500 focus:border-red-500",
                    passwordTouched && passwordResult?.valid && "border-green-500 focus:border-green-500"
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
              {/* Password strength indicator */}
              {password && (
                <PasswordStrengthIndicator
                  password={password}
                  strength={passwordResult?.strength}
                  requirements={passwordResult?.requirements}
                  lang={lang}
                />
              )}
            </div>

            <div className="gap-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">{t('Confirm Password', '确认密码')}</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder={t('Re-enter password', '再次输入密码')}
                  value={confirmPassword}
                  maxLength={100}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  onFocus={() => { isTypingRef.current = true; isPasswordFieldRef.current = true; setIsLookingAway(true); setConfirmPasswordTouched(true); }}
                  onBlur={() => { isTypingRef.current = false; isPasswordFieldRef.current = false; setIsLookingAway(false); }}
                  className={cn(
                    "h-12 pr-10 bg-background border-border/60 focus:border-primary",
                    confirmPasswordTouched && confirmPasswordError && "border-red-500 focus:border-red-500",
                    confirmPasswordTouched && !confirmPasswordError && confirmPassword && "border-green-500 focus:border-green-500"
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
                {confirmPasswordTouched && !confirmPasswordError && confirmPassword && (
                  <CheckCircle2 className="absolute right-10 top-1/2 -translate-y-1/2 size-4 text-green-500" />
                )}
              </div>
              {confirmPasswordTouched && confirmPasswordError && (
                <p className="text-xs text-red-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" />
                  {confirmPasswordError}
                </p>
              )}
            </div>

            <div className="flex items-center">
              <Checkbox
                id="terms"
                checked={agreedToTerms}
                onCheckedChange={(checked) => setAgreedToTerms(checked === true)}
              />
              <Label htmlFor="terms" className="ml-2 text-sm text-muted-foreground cursor-pointer">
                {t('I agree to the', '我同意')} <button type="button" className="text-primary hover:underline bg-transparent border-none cursor-pointer">{t('Terms of Service', '服务条款')}</button> {t('and', '和')} <button type="button" className="text-primary hover:underline bg-transparent border-none cursor-pointer">{t('Privacy Policy', '隐私政策')}</button>
              </Label>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base font-medium"
              size="lg"
              disabled={isPending}
            >
              {isPending ? (t('Creating account...', '创建中...')) : (t('Create account', '注册'))}
            </Button>
          </form>

          {/* Sign In Link */}
          <div className="text-center text-sm text-muted-foreground mt-8">
            {t('Already have an account?', '已有账号？')}{" "}
            <Link href="/login" className="text-foreground font-medium hover:underline">
              {t('Sign in', '立即登录')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export const Component = RegisterPage;
