"use client";

import { useState, useEffect, useRef } from "react";
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


interface PupilProps {
  size?: number;
  maxDistance?: number;
  pupilColor?: string;
  forceLookX?: number;
  forceLookY?: number;
}

const Pupil = ({
  size = 12,
  maxDistance = 5,
  pupilColor = "black",
  forceLookX,
  forceLookY
}: PupilProps) => {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const pupilRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const calculatePupilPosition = () => {
    if (!pupilRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const pupil = pupilRef.current.getBoundingClientRect();
    const pupilCenterX = pupil.left + pupil.width / 2;
    const pupilCenterY = pupil.top + pupil.height / 2;

    const deltaX = mouseX - pupilCenterX;
    const deltaY = mouseY - pupilCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={pupilRef}
      className="rounded-full"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: pupilColor,
        transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
        transition: 'transform 0.1s ease-out',
      }}
    />
  );
};




interface EyeBallProps {
  size?: number;
  pupilSize?: number;
  maxDistance?: number;
  eyeColor?: string;
  pupilColor?: string;
  isBlinking?: boolean;
  forceLookX?: number;
  forceLookY?: number;
}

const EyeBall = ({
  size = 48,
  pupilSize = 16,
  maxDistance = 10,
  eyeColor = "white",
  pupilColor = "black",
  isBlinking = false,
  forceLookX,
  forceLookY
}: EyeBallProps) => {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const eyeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const calculatePupilPosition = () => {
    if (!eyeRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const eye = eyeRef.current.getBoundingClientRect();
    const eyeCenterX = eye.left + eye.width / 2;
    const eyeCenterY = eye.top + eye.height / 2;

    const deltaX = mouseX - eyeCenterX;
    const deltaY = mouseY - eyeCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={eyeRef}
      className="rounded-full flex items-center justify-center transition-all duration-150"
      style={{
        width: `${size}px`,
        height: isBlinking ? '2px' : `${size}px`,
        backgroundColor: eyeColor,
        overflow: 'hidden',
      }}
    >
      {!isBlinking && (
        <div
          className="rounded-full"
          style={{
            width: `${pupilSize}px`,
            height: `${pupilSize}px`,
            backgroundColor: pupilColor,
            transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
            transition: 'transform 0.1s ease-out',
          }}
        />
      )}
    </div>
  );
};

function RegisterPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const [isPurpleBlinking, setIsPurpleBlinking] = useState(false);
  const [isBlackBlinking, setIsBlackBlinking] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isPasswordField, setIsPasswordField] = useState(false);
  const [isLookingAway, setIsLookingAway] = useState(false);
  const [lang, setLang] = useState<'en' | 'zh'>('zh');
  const purpleRef = useRef<HTMLDivElement>(null);
  const blackRef = useRef<HTMLDivElement>(null);
  const yellowRef = useRef<HTMLDivElement>(null);
  const orangeRef = useRef<HTMLDivElement>(null);

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

  const toggleLang = () => setLang(lang === 'en' ? 'zh' : 'en');
  const t = (en: string, zh: string) => lang === 'en' ? en : zh;

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Blinking effect for purple character
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsPurpleBlinking(true);
        setTimeout(() => {
          setIsPurpleBlinking(false);
          scheduleBlink();
        }, 150);
      }, getRandomBlinkInterval());

      return blinkTimeout;
    };

    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  // Blinking effect for black character
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsBlackBlinking(true);
        setTimeout(() => {
          setIsBlackBlinking(false);
          scheduleBlink();
        }, 150);
      }, getRandomBlinkInterval());

      return blinkTimeout;
    };

    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  // Password privacy - look away
  useEffect(() => {
    if (isPasswordField) {
      setIsLookingAway(true);
    } else {
      setIsLookingAway(false);
    }
  }, [isPasswordField]);

  // Real-time validation
  useEffect(() => {
    if (emailTouched && email) {
      const result = validateEmail(email);
      setEmailError(result.valid ? null : result.error || null);
    }
  }, [email, emailTouched]);

  useEffect(() => {
    if (usernameTouched && username) {
      const result = validateUsername(username);
      setUsernameError(result.valid ? null : result.error || null);
    }
  }, [username, usernameTouched]);

  useEffect(() => {
    if (passwordTouched && password) {
      const result = validatePassword(password);
      setPasswordResult(result);
    } else {
      setPasswordResult(null);
    }
  }, [password, passwordTouched]);

  useEffect(() => {
    if (confirmPasswordTouched && confirmPassword) {
      const result = validatePasswordConfirm(password, confirmPassword);
      setConfirmPasswordError(result.valid ? null : result.error || null);
    }
  }, [password, confirmPassword, confirmPasswordTouched]);

  const calculatePosition = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return { faceX: 0, faceY: 0, bodyRotation: 0 };

    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 3;

    const deltaX = mouseX - centerX;
    const deltaY = mouseY - centerY;

    const faceX = Math.max(-15, Math.min(15, deltaX / 20));
    const faceY = Math.max(-10, Math.min(10, deltaY / 30));
    const bodySkew = Math.max(-6, Math.min(6, -deltaX / 120));

    return { faceX, faceY, bodySkew };
  };

  const purplePos = calculatePosition(purpleRef);
  const blackPos = calculatePosition(blackRef);
  const yellowPos = calculatePosition(yellowRef);
  const orangePos = calculatePosition(orangeRef);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Mark all fields as touched to show validation errors
    setEmailTouched(true);
    setUsernameTouched(true);
    setPasswordTouched(true);
    setConfirmPasswordTouched(true);

    // Validate all fields
    const emailResult = validateEmail(email);
    const usernameResult = validateUsername(username);
    const passwordRes = validatePassword(password);
    const confirmResult = validatePasswordConfirm(password, confirmPassword);

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

    setIsLoading(true);

    try {
      await register(email, username, password);
      router.push("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("Registration failed. Please try again.", "注册失败，请重试。"));
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
          {/* Cartoon Characters */}
          <div className="relative" style={{ width: '550px', height: '400px' }}>
            {/* Purple tall rectangle character - Back layer */}
            <div
              ref={purpleRef}
              className="absolute bottom-0 transition-all duration-500 ease-out"
              style={{
                left: '70px',
                width: '180px',
                height: '400px',
                backgroundColor: '#6C3FF5',
                borderRadius: '10px 10px 0 0',
                zIndex: 1,
                transform: isLookingAway
                  ? `translateX(-25px)`
                  : `skewX(${purplePos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              <div
                className="absolute flex gap-8 transition-all duration-300"
                style={{
                  left: `${45 + (isLookingAway ? -15 : purplePos.faceX)}px`,
                  top: `${40 + (isLookingAway ? 5 : purplePos.faceY)}px`,
                }}
              >
                <EyeBall
                  size={18}
                  pupilSize={7}
                  maxDistance={5}
                  eyeColor="white"
                  pupilColor="#2D2D2D"
                  isBlinking={isPurpleBlinking}
                  forceLookX={isLookingAway ? -8 : undefined}
                  forceLookY={isLookingAway ? 2 : undefined}
                />
                <EyeBall
                  size={18}
                  pupilSize={7}
                  maxDistance={5}
                  eyeColor="white"
                  pupilColor="#2D2D2D"
                  isBlinking={isPurpleBlinking}
                  forceLookX={isLookingAway ? -8 : undefined}
                  forceLookY={isLookingAway ? 2 : undefined}
                />
              </div>
            </div>

            {/* Black tall rectangle character - Middle layer */}
            <div
              ref={blackRef}
              className="absolute bottom-0 transition-all duration-500 ease-out"
              style={{
                left: '240px',
                width: '120px',
                height: '310px',
                backgroundColor: '#2D2D2D',
                borderRadius: '8px 8px 0 0',
                zIndex: 2,
                transform: isLookingAway
                  ? `translateX(-15px)`
                  : `skewX(${blackPos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              <div
                className="absolute flex gap-6 transition-all duration-300"
                style={{
                  left: `${26 + (isLookingAway ? -12 : blackPos.faceX)}px`,
                  top: `${32 + (isLookingAway ? 4 : blackPos.faceY)}px`,
                }}
              >
                <EyeBall
                  size={16}
                  pupilSize={6}
                  maxDistance={4}
                  eyeColor="white"
                  pupilColor="#2D2D2D"
                  isBlinking={isBlackBlinking}
                  forceLookX={isLookingAway ? -7 : undefined}
                  forceLookY={isLookingAway ? 2 : undefined}
                />
                <EyeBall
                  size={16}
                  pupilSize={6}
                  maxDistance={4}
                  eyeColor="white"
                  pupilColor="#2D2D2D"
                  isBlinking={isBlackBlinking}
                  forceLookX={isLookingAway ? -7 : undefined}
                  forceLookY={isLookingAway ? 2 : undefined}
                />
              </div>
            </div>

            {/* Orange semi-circle character - Front left */}
            <div
              ref={orangeRef}
              className="absolute bottom-0 transition-all duration-500 ease-out"
              style={{
                left: '0px',
                width: '240px',
                height: '200px',
                zIndex: 3,
                backgroundColor: '#FF9B6B',
                borderRadius: '120px 120px 0 0',
                transform: isLookingAway
                  ? `translateX(-10px)`
                  : `skewX(${orangePos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              <div
                className="absolute flex gap-8 transition-all duration-300"
                style={{
                  left: `${82 + (isLookingAway ? -20 : (orangePos.faceX || 0))}px`,
                  top: `${90 + (isLookingAway ? 5 : (orangePos.faceY || 0))}px`,
                }}
              >
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
              </div>
            </div>

            {/* Yellow tall rectangle character - Front right */}
            <div
              ref={yellowRef}
              className="absolute bottom-0 transition-all duration-500 ease-out"
              style={{
                left: '310px',
                width: '140px',
                height: '230px',
                backgroundColor: '#E8D754',
                borderRadius: '70px 70px 0 0',
                zIndex: 4,
                transform: isLookingAway
                  ? `translateX(-20px)`
                  : `skewX(${yellowPos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              <div
                className="absolute flex gap-6 transition-all duration-300"
                style={{
                  left: `${52 + (isLookingAway ? -18 : (yellowPos.faceX || 0))}px`,
                  top: `${40 + (isLookingAway ? 5 : (yellowPos.faceY || 0))}px`,
                }}
              >
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
              </div>
              <div
                className="absolute w-20 h-[4px] bg-[#2D2D2D] rounded-full transition-all duration-300"
                style={{
                  left: `${40 + (isLookingAway ? -15 : (yellowPos.faceX || 0))}px`,
                  top: `${88 + (isLookingAway ? 5 : (yellowPos.faceY || 0))}px`,
                }}
              />
            </div>
          </div>
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

      {/* Right Register Section */}
      <div className="flex items-center justify-center p-8 bg-background relative">
        {/* Language Switcher - Top Right Corner */}
        <div className="absolute top-6 right-6">
          <div className="inline-flex items-center bg-secondary rounded-full p-1">
            <button
              onClick={() => setLang('zh')}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${
                lang === 'zh'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              中文
            </button>
            <button
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
            <span>{t('DSA Platform', 'DSA 教学平台')}</span>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold tracking-tight mb-2">{t('Create your account', '创建账号')}</h1>
            <p className="text-muted-foreground text-sm">{t('Join our learning platform', '加入我们的学习平台')}</p>
          </div>

          {/* Register Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">{t('Username', '用户名')}</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="username"
                  type="text"
                  placeholder={t('yourname', 'username')}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => { setIsTyping(false); setUsernameTouched(true); }}
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

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">{t('Email', '邮箱地址')}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder={t('you@example.com', 'you@example.com')}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => { setIsTyping(false); setEmailTouched(true); }}
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
                  placeholder={t('Min. 8 characters', '至少8个字符')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => { setIsTyping(true); setIsPasswordField(true); setPasswordTouched(true); }}
                  onBlur={() => { setIsTyping(false); setIsPasswordField(false); }}
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

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">{t('Confirm Password', '确认密码')}</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder={t('Re-enter password', '再次输入密码')}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  onFocus={() => { setIsTyping(true); setIsPasswordField(true); setConfirmPasswordTouched(true); }}
                  onBlur={() => { setIsTyping(false); setIsPasswordField(false); }}
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
              <Checkbox id="terms" />
              <Label htmlFor="terms" className="ml-2 text-sm text-muted-foreground cursor-pointer">
                {t('I agree to the', '我同意')} <a href="#" className="text-primary hover:underline">{t('Terms of Service', '服务条款')}</a> {t('and', '和')} <a href="#" className="text-primary hover:underline">{t('Privacy Policy', '隐私政策')}</a>
              </Label>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base font-medium"
              size="lg"
              disabled={isLoading}
            >
              {isLoading ? (t('Creating account...', '创建中...')) : (t('Create account', '注册'))}
            </Button>
          </form>

          {/* Sign In Link */}
          <div className="text-center text-sm text-muted-foreground mt-8">
            {t('Already have an account?', '已有账号？')}{" "}
            <a href="/login" className="text-foreground font-medium hover:underline">
              {t('Sign in', '立即登录')}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export const Component = RegisterPage;
