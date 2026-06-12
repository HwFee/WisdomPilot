"use client";

import { useCallback, useReducer, useRef } from "react";
import type {
  BaseAnswersSubmitResponse,
  BaseQuestionResponse,
  CourseDetailResponse,
  MasteryOverviewResponse,
  NoteResponse,
} from "@/types/api";
import type { MasteryStep } from "../types";

// --- State shape ---

export type MasteryPathState = {
  // Loading & overview
  loading: boolean;
  overview: MasteryOverviewResponse | null;
  courseDetail: CourseDetailResponse | null;
  // Chapter selection
  selectedChapterId: number | null;
  selectedChapterTitle: string;
  selectedSectionId: number | null;
  step: MasteryStep;
  // Base quiz
  baseQuestions: BaseQuestionResponse[];
  baseQuestionLoading: boolean;
  currentQuestionIndex: number;
  baseResult: BaseAnswersSubmitResponse | null;
  // Notes
  showNoteEditor: boolean;
  editingNote: NoteResponse | null;
  noteRefreshKey: number;
};

const INITIAL_STATE: MasteryPathState = {
  loading: true,
  overview: null,
  courseDetail: null,
  selectedChapterId: null,
  selectedChapterTitle: "",
  selectedSectionId: null,
  step: "select_chapter",
  baseQuestions: [],
  baseQuestionLoading: false,
  currentQuestionIndex: 0,
  baseResult: null,
  showNoteEditor: false,
  editingNote: null,
  noteRefreshKey: 0,
};

// --- Action shape ---

export type MasteryPathAction =
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_OVERVIEW"; payload: MasteryOverviewResponse | null }
  | { type: "SET_COURSE_DETAIL"; payload: CourseDetailResponse | null }
  | { type: "SET_SELECTED_CHAPTER_ID"; payload: number | null }
  | { type: "SET_SELECTED_CHAPTER_TITLE"; payload: string }
  | { type: "SET_SELECTED_SECTION_ID"; payload: number | null }
  | { type: "SET_STEP"; payload: MasteryStep }
  | {
      type: "SET_BASE_QUESTIONS";
      payload: BaseQuestionResponse[];
    }
  | { type: "SET_BASE_QUESTION_LOADING"; payload: boolean }
  | { type: "SET_CURRENT_QUESTION_INDEX"; payload: number }
  | {
      type: "SET_BASE_RESULT";
      payload: BaseAnswersSubmitResponse | null;
    }
  | { type: "SET_SHOW_NOTE_EDITOR"; payload: boolean }
  | { type: "SET_EDITING_NOTE"; payload: NoteResponse | null }
  | { type: "SET_NOTE_REFRESH_KEY"; payload: number };

// --- Reducer ---

function reducer(state: MasteryPathState, action: MasteryPathAction): MasteryPathState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, loading: action.payload };
    case "SET_OVERVIEW":
      return { ...state, overview: action.payload };
    case "SET_COURSE_DETAIL":
      return { ...state, courseDetail: action.payload };
    case "SET_SELECTED_CHAPTER_ID":
      return { ...state, selectedChapterId: action.payload };
    case "SET_SELECTED_CHAPTER_TITLE":
      return { ...state, selectedChapterTitle: action.payload };
    case "SET_SELECTED_SECTION_ID":
      return { ...state, selectedSectionId: action.payload };
    case "SET_STEP":
      return { ...state, step: action.payload };
    case "SET_BASE_QUESTIONS":
      return { ...state, baseQuestions: action.payload };
    case "SET_BASE_QUESTION_LOADING":
      return { ...state, baseQuestionLoading: action.payload };
    case "SET_CURRENT_QUESTION_INDEX":
      return { ...state, currentQuestionIndex: action.payload };
    case "SET_BASE_RESULT":
      return { ...state, baseResult: action.payload };
    case "SET_SHOW_NOTE_EDITOR":
      return { ...state, showNoteEditor: action.payload };
    case "SET_EDITING_NOTE":
      return { ...state, editingNote: action.payload };
    case "SET_NOTE_REFRESH_KEY":
      return { ...state, noteRefreshKey: action.payload };
    default:
      return state;
  }
}

// --- Setter callbacks (stable references) ---

type Dispatch<T> = (value: T | ((prev: T) => T)) => void;

export type MasteryPathSetters = {
  setLoading: Dispatch<boolean>;
  setOverview: Dispatch<MasteryOverviewResponse | null>;
  setCourseDetail: Dispatch<CourseDetailResponse | null>;
  setSelectedChapterId: Dispatch<number | null>;
  setSelectedChapterTitle: Dispatch<string>;
  setSelectedSectionId: Dispatch<number | null>;
  setStep: Dispatch<MasteryStep>;
  setBaseQuestions: Dispatch<BaseQuestionResponse[]>;
  setBaseQuestionLoading: Dispatch<boolean>;
  setCurrentQuestionIndex: Dispatch<number>;
  setBaseResult: Dispatch<BaseAnswersSubmitResponse | null>;
  setShowNoteEditor: Dispatch<boolean>;
  setEditingNote: Dispatch<NoteResponse | null>;
  setNoteRefreshKey: Dispatch<number>;
};

export function useMasteryPathState(): {
  state: MasteryPathState;
  setters: MasteryPathSetters;
} {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  // Ref to current state so setter callbacks can resolve function-form updates
  // without changing identity when state changes.
  const stateRef = useRef(state);
  stateRef.current = state;

  const setLoading = useCallback<MasteryPathSetters["setLoading"]>(
    (value) =>
      dispatch({
        type: "SET_LOADING",
        payload:
          typeof value === "function"
            ? (value as (prev: boolean) => boolean)(stateRef.current.loading)
            : value,
      }),
    [],
  );
  const setOverview = useCallback<MasteryPathSetters["setOverview"]>(
    (value) =>
      dispatch({
        type: "SET_OVERVIEW",
        payload:
          typeof value === "function"
            ? (value as (prev: MasteryOverviewResponse | null) => MasteryOverviewResponse | null)(
                stateRef.current.overview,
              )
            : value,
      }),
    [],
  );
  const setCourseDetail = useCallback<MasteryPathSetters["setCourseDetail"]>(
    (value) =>
      dispatch({
        type: "SET_COURSE_DETAIL",
        payload:
          typeof value === "function"
            ? (value as (prev: CourseDetailResponse | null) => CourseDetailResponse | null)(
                stateRef.current.courseDetail,
              )
            : value,
      }),
    [],
  );
  const setSelectedChapterId = useCallback<MasteryPathSetters["setSelectedChapterId"]>(
    (value) =>
      dispatch({
        type: "SET_SELECTED_CHAPTER_ID",
        payload:
          typeof value === "function"
            ? (value as (prev: number | null) => number | null)(
                stateRef.current.selectedChapterId,
              )
            : value,
      }),
    [],
  );
  const setSelectedChapterTitle = useCallback<MasteryPathSetters["setSelectedChapterTitle"]>(
    (value) =>
      dispatch({
        type: "SET_SELECTED_CHAPTER_TITLE",
        payload:
          typeof value === "function"
            ? (value as (prev: string) => string)(
                stateRef.current.selectedChapterTitle,
              )
            : value,
      }),
    [],
  );
  const setSelectedSectionId = useCallback<MasteryPathSetters["setSelectedSectionId"]>(
    (value) =>
      dispatch({
        type: "SET_SELECTED_SECTION_ID",
        payload:
          typeof value === "function"
            ? (value as (prev: number | null) => number | null)(
                stateRef.current.selectedSectionId,
              )
            : value,
      }),
    [],
  );
  const setStep = useCallback<MasteryPathSetters["setStep"]>(
    (value) =>
      dispatch({
        type: "SET_STEP",
        payload:
          typeof value === "function"
            ? (value as (prev: MasteryStep) => MasteryStep)(stateRef.current.step)
            : value,
      }),
    [],
  );
  const setBaseQuestions = useCallback<MasteryPathSetters["setBaseQuestions"]>(
    (value) =>
      dispatch({
        type: "SET_BASE_QUESTIONS",
        payload:
          typeof value === "function"
            ? (value as (prev: BaseQuestionResponse[]) => BaseQuestionResponse[])(
                stateRef.current.baseQuestions,
              )
            : value,
      }),
    [],
  );
  const setBaseQuestionLoading = useCallback<MasteryPathSetters["setBaseQuestionLoading"]>(
    (value) =>
      dispatch({
        type: "SET_BASE_QUESTION_LOADING",
        payload:
          typeof value === "function"
            ? (value as (prev: boolean) => boolean)(
                stateRef.current.baseQuestionLoading,
              )
            : value,
      }),
    [],
  );
  const setCurrentQuestionIndex = useCallback<MasteryPathSetters["setCurrentQuestionIndex"]>(
    (value) =>
      dispatch({
        type: "SET_CURRENT_QUESTION_INDEX",
        payload:
          typeof value === "function"
            ? (value as (prev: number) => number)(
                stateRef.current.currentQuestionIndex,
              )
            : value,
      }),
    [],
  );
  const setBaseResult = useCallback<MasteryPathSetters["setBaseResult"]>(
    (value) =>
      dispatch({
        type: "SET_BASE_RESULT",
        payload:
          typeof value === "function"
            ? (value as (prev: BaseAnswersSubmitResponse | null) => BaseAnswersSubmitResponse | null)(
                stateRef.current.baseResult,
              )
            : value,
      }),
    [],
  );
  const setShowNoteEditor = useCallback<MasteryPathSetters["setShowNoteEditor"]>(
    (value) =>
      dispatch({
        type: "SET_SHOW_NOTE_EDITOR",
        payload:
          typeof value === "function"
            ? (value as (prev: boolean) => boolean)(
                stateRef.current.showNoteEditor,
              )
            : value,
      }),
    [],
  );
  const setEditingNote = useCallback<MasteryPathSetters["setEditingNote"]>(
    (value) =>
      dispatch({
        type: "SET_EDITING_NOTE",
        payload:
          typeof value === "function"
            ? (value as (prev: NoteResponse | null) => NoteResponse | null)(
                stateRef.current.editingNote,
              )
            : value,
      }),
    [],
  );
  const setNoteRefreshKey = useCallback<MasteryPathSetters["setNoteRefreshKey"]>(
    (value) =>
      dispatch({
        type: "SET_NOTE_REFRESH_KEY",
        payload:
          typeof value === "function"
            ? (value as (prev: number) => number)(stateRef.current.noteRefreshKey)
            : value,
      }),
    [],
  );

  return {
    state,
    setters: {
      setLoading,
      setOverview,
      setCourseDetail,
      setSelectedChapterId,
      setSelectedChapterTitle,
      setSelectedSectionId,
      setStep,
      setBaseQuestions,
      setBaseQuestionLoading,
      setCurrentQuestionIndex,
      setBaseResult,
      setShowNoteEditor,
      setEditingNote,
      setNoteRefreshKey,
    },
  };
}
