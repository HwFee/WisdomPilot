"use client";

import { Code2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

import { LANGUAGE_OPTIONS, type RightPanelTab, type TestCaseResult } from "../types";

export type MobileTab = "problem" | "code" | "output";

export interface ArenaMainContentProps {
  problemPanel: React.ReactNode;
  codeEditor: React.ReactNode;
  outputContent: React.ReactNode;
  mobileTab: MobileTab;
  setMobileTab: (tab: MobileTab) => void;
  language: string;
  onLanguageChange: (lang: string) => void;
  rightPanelTab: RightPanelTab;
  setRightPanelTab: (tab: RightPanelTab) => void;
  testResults: TestCaseResult[];
}

export function ArenaMainContent({
  problemPanel,
  codeEditor,
  outputContent,
  mobileTab,
  setMobileTab,
  language,
  onLanguageChange,
  rightPanelTab,
  setRightPanelTab,
  testResults,
}: ArenaMainContentProps) {
  return (
    <main className="flex-1 min-h-0 overflow-hidden">
      {/* Desktop: 3-column grid */}
      <div className="h-full hidden lg:grid grid-cols-12 gap-0">
        {/* Problem */}
        <div className="col-span-4 ide-problem-panel">
          {problemPanel}
        </div>

        {/* Code Editor */}
        <div className="col-span-5 ide-editor-panel flex flex-col">
          <div className="flex-shrink-0 flex items-center justify-between px-3 py-2 border-b border-border bg-card">
            <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Code2 className="size-4" strokeWidth={1.5} />
              代码
            </span>
            <select
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              className="px-2 py-1 text-xs font-medium text-muted-foreground bg-card border border-border rounded-md focus:outline-none focus:border-primary cursor-pointer"
            >
              {LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang.key} value={lang.key}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-h-0">
            {codeEditor}
          </div>
        </div>

        {/* Output / Tests */}
        <div className="col-span-3 bg-card border-l border-border flex flex-col">
          <div className="panel-tabs flex-shrink-0 flex items-center">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setRightPanelTab("code")}
              className={`panel-tab rounded-none ${rightPanelTab !== "output" ? "active" : ""}`}
            >
              <Code2 className="size-4 mr-1.5" strokeWidth={1.5} />
              测试
            </Button>
            {testResults.length > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setRightPanelTab("output")}
                className={`panel-tab rounded-none ${rightPanelTab === "output" ? "active" : ""}`}
              >
                <CheckCircle className="size-4 mr-1.5" strokeWidth={1.5} />
                结果
              </Button>
            )}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            {outputContent}
          </div>
        </div>
      </div>

      {/* Mobile/Tablet: tabs */}
      <div className="h-full flex flex-col lg:hidden">
        <div className="flex border-b border-border bg-card">
          <Button
            type="button"
            variant="ghost"
            onClick={() => setMobileTab("problem")}
            className={`flex-1 rounded-none h-auto py-3 text-xs font-medium ${mobileTab === "problem" ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            题目
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => setMobileTab("code")}
            className={`flex-1 rounded-none h-auto py-3 text-xs font-medium ${mobileTab === "code" ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            代码
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => setMobileTab("output")}
            className={`flex-1 rounded-none h-auto py-3 text-xs font-medium ${mobileTab === "output" ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            输出
          </Button>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          {mobileTab === "problem" && (
            <div className="h-full ide-problem-panel overflow-y-auto">
              {problemPanel}
            </div>
          )}
          {mobileTab === "code" && (
            <div className="h-full flex flex-col ide-editor-panel">
              <div className="flex-shrink-0 flex items-center justify-between px-3 py-2 border-b border-border bg-card">
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <Code2 className="size-4" strokeWidth={1.5} />
                  代码
                </span>
                <select
                  value={language}
                  onChange={(e) => onLanguageChange(e.target.value)}
                  className="px-2 py-1 text-xs font-medium text-muted-foreground bg-card border border-border rounded-md focus:outline-none focus:border-primary cursor-pointer"
                >
                  {LANGUAGE_OPTIONS.map((lang) => (
                    <option key={lang.key} value={lang.key}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1 min-h-0">
                {codeEditor}
              </div>
            </div>
          )}
          {mobileTab === "output" && (
            <div className="h-full bg-card overflow-y-auto">
              {outputContent}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
