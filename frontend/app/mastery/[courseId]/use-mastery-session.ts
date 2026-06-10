"use client";

import { useRef, useCallback } from "react";
import {
  getStoredToken,
  startLearningSession,
  endLearningSession,
} from "@/lib/api";
import { endLearningSessionKeepalive } from "@/lib/api/stats";

export function useMasterySession(getSearchParam: (name: string) => string | null) {
  const sessionStartedAtRef = useRef<number | null>(null);
  const activeSessionChapterIdRef = useRef<number | null>(null);
  const sessionInitializedRef = useRef(false);
  const sessionEndedRef = useRef(false);
  const currentSectionIdRef = useRef<number | null>(null);

  const startTrackedSession = useCallback(async (chapterId: number) => {
    const token = getStoredToken();
    if (!token) return;

    const continueSession = getSearchParam("continueSession") === "1";
    if (continueSession) {
      try {
        const savedSession = localStorage.getItem("masterySession:v1");
        if (savedSession) {
          const sessionData = JSON.parse(savedSession);
          activeSessionChapterIdRef.current = sessionData.chapterId;
          sessionStartedAtRef.current = sessionData.startedAt;
          sessionInitializedRef.current = true;
          sessionEndedRef.current = false;
          localStorage.removeItem("masterySession:v1");
          return;
        }
      } catch (e) {
        console.error("[精进之路-学习时长] 解析会话数据失败:", e);
      }
    }

    if (
      activeSessionChapterIdRef.current === chapterId &&
      sessionStartedAtRef.current
    ) {
      return;
    }

    if (
      activeSessionChapterIdRef.current !== null &&
      sessionStartedAtRef.current
    ) {
      const prevChapterId = activeSessionChapterIdRef.current ?? undefined;
      const durationSeconds = Math.max(
        1,
        Math.floor((Date.now() - sessionStartedAtRef.current) / 1000),
      );
      activeSessionChapterIdRef.current = null;
      sessionStartedAtRef.current = null;
      sessionInitializedRef.current = false;
      try {
        await endLearningSession(token, durationSeconds, prevChapterId);
      } catch (error) {
        console.error("[精进之路] 结束上一段学习会话失败:", error);
      }
    }

    try {
      await startLearningSession(token, chapterId, 0);
      const now = Date.now();
      activeSessionChapterIdRef.current = chapterId;
      sessionStartedAtRef.current = now;
      sessionInitializedRef.current = true;
      sessionEndedRef.current = false;
    } catch (error) {
      console.error("[精进之路] 开始学习会话失败:", error);
    }
  }, [getSearchParam]);

  const endTrackedSession = useCallback(async () => {
    if (sessionEndedRef.current) {
      return;
    }

    const token = getStoredToken();
    const startedAt = sessionStartedAtRef.current;

    if (!token || !startedAt || !sessionInitializedRef.current) {
      return;
    }

    const durationSeconds = Math.max(
      1,
      Math.floor((Date.now() - startedAt) / 1000),
    );
    const chapterId = activeSessionChapterIdRef.current;

    sessionEndedRef.current = true;
    sessionInitializedRef.current = false;
    activeSessionChapterIdRef.current = null;
    sessionStartedAtRef.current = null;

    endLearningSessionKeepalive(token, durationSeconds, chapterId ?? undefined);
  }, []);

  return {
    sessionStartedAtRef,
    activeSessionChapterIdRef,
    sessionInitializedRef,
    sessionEndedRef,
    currentSectionIdRef,
    startTrackedSession,
    endTrackedSession,
  };
}
