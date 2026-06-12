"use client";

import { CodeEditorPanel } from "@/components/exercise/CodeEditorPanel";
import { LANGUAGE_MAP } from "../types";

export interface ArenaCodePanelProps {
  code: string;
  setCode: (value: string) => void;
  language: string;
}

export function ArenaCodePanel({ code, setCode, language }: ArenaCodePanelProps) {
  return (
    <CodeEditorPanel
      value={code}
      onChange={setCode}
      language={LANGUAGE_MAP[language]?.monaco || "python"}
    />
  );
}
