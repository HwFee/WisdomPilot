/**
 * Exercise WebSocket Client - 题目生成实时推送客户端
 *
 * 提供：
 * 1. WebSocket连接管理
 * 2. 题目生成状态跟踪
 * 3. 轮询备选机制
 *
 * 简化实现，优先稳定性。
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// API基础URL（从环境变量获取）
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_BASE_URL.replace(/^http/, 'ws') + '/ws/exercises';

// 消息类型
export interface ExerciseGeneratedMessage {
  type: 'exercise_generated';
  session_id: string;
  index: number;
  exercise: Exercise;
  progress: number;
}

export interface GenerationCompletedMessage {
  type: 'generation_completed';
  session_id: string;
  total_count: number;
}

export interface GenerationFailedMessage {
  type: 'generation_failed';
  session_id: string;
  error: string;
}

export type ExerciseStreamMessage =
  | ExerciseGeneratedMessage
  | GenerationCompletedMessage
  | GenerationFailedMessage;

// 题目类型
export interface Exercise {
  id: string;
  type: 'choice' | 'programming' | 'fill_blank';
  text: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  knowledge_points: string[];
  difficulty: number;
}

// 状态类型
export interface ExerciseStreamState {
  sessionId: string | null;
  exercises: Exercise[];
  totalCount: number;
  generatedCount: number;
  status: 'idle' | 'connecting' | 'generating' | 'completed' | 'failed';
  error: string | null;
}

/**
 * 使用WebSocket接收流式生成的题目
 */
export function useExerciseStream() {
  const [state, setState] = useState<ExerciseStreamState>({
    sessionId: null,
    exercises: [],
    totalCount: 0,
    generatedCount: 0,
    status: 'idle',
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * 建立WebSocket连接
   */
  const connect = useCallback((token: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setState(prev => ({ ...prev, status: 'connecting' }));

    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[ExerciseWebSocket] 连接成功');
      setState(prev => ({ ...prev, status: 'generating' }));

      // 启动心跳
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      const data = event.data;

      // 处理心跳响应
      if (data === 'pong') return;

      try {
        const message: ExerciseStreamMessage = JSON.parse(data);
        handleMessage(message);
      } catch (e) {
        console.error('[ExerciseWebSocket] 消息解析失败:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('[ExerciseWebSocket] 连接错误:', error);
      setState(prev => ({
        ...prev,
        status: prev.status === 'generating' ? prev.status : 'failed',
        error: 'WebSocket连接错误',
      }));
    };

    ws.onclose = () => {
      console.log('[ExerciseWebSocket] 连接关闭');
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
    };
  }, []);

  /**
   * 处理WebSocket消息
   */
  const handleMessage = useCallback((message: ExerciseStreamMessage) => {
    switch (message.type) {
      case 'exercise_generated':
        setState(prev => ({
          ...prev,
          sessionId: message.session_id,
          exercises: [...prev.exercises, message.exercise],
          generatedCount: message.progress,
          status: 'generating',
        }));
        break;

      case 'generation_completed':
        setState(prev => ({
          ...prev,
          totalCount: message.total_count,
          status: 'completed',
        }));
        break;

      case 'generation_failed':
        setState(prev => ({
          ...prev,
          status: 'failed',
          error: message.error,
        }));
        break;
    }
  }, []);

  /**
   * 断开WebSocket连接
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  /**
   * 重置状态
   */
  const reset = useCallback(() => {
    disconnect();
    setState({
      sessionId: null,
      exercises: [],
      totalCount: 0,
      generatedCount: 0,
      status: 'idle',
      error: null,
    });
  }, [disconnect]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    reset,
  };
}

/**
 * 轮询获取生成状态（WebSocket的备选方案）
 */
export async function getGenerationStatus(
  sessionId: string,
  token: string
): Promise<{
  session_id: string;
  status: string;
  total_count: number;
  generated_count: number;
  exercises: Exercise[];
  is_completed: boolean;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/learning-path/mastery/generation-status/${sessionId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('获取生成状态失败');
  }

  return response.json();
}

/**
 * 轮询获取会话所有题目
 */
export async function getSessionExercises(
  sessionId: string,
  token: string
): Promise<{
  session_id: string;
  questions: Exercise[];
  total_count: number;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/learning-path/mastery/generation/${sessionId}/exercises`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('获取会话题目失败');
  }

  return response.json();
}
