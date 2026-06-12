"use client";

import { LuoguTestCaseTable } from "@/components/exercise/LuoguTestCaseTable";
import {
  CustomTestInput,
  TestOutputDisplay,
} from "@/components/exercise/CustomTestInput";
import type { TestCaseResult, RightPanelTab } from "../types";

export interface CustomTestOutputShape {
  output?: string;
  expected?: string;
  passed?: boolean;
  error?: string;
}

export interface ArenaOutputPanelProps {
  rightPanelTab: RightPanelTab;
  testResults: TestCaseResult[];
  isSubmitting: boolean;
  handleCustomRun: (input: string, isFromSample?: boolean) => Promise<void>;
  isCustomRunning: boolean;
  customTestInput: string;
  customTestOutput: CustomTestOutputShape | null;
}

export function ArenaOutputPanel({
  rightPanelTab,
  testResults,
  isSubmitting,
  handleCustomRun,
  isCustomRunning,
  customTestInput,
  customTestOutput,
}: ArenaOutputPanelProps) {
  if (rightPanelTab === "output" && testResults.length > 0) {
    return (
      <div className="p-4 bg-background">
        <LuoguTestCaseTable
          results={testResults}
          passedCount={testResults.filter((r) => r.passed).length}
          totalCount={testResults.length}
          isRunning={isSubmitting}
        />
      </div>
    );
  }

  return (
    <div>
      <CustomTestInput
        onRun={(input) => handleCustomRun(input, false)}
        isRunning={isCustomRunning}
        defaultInput={customTestInput}
      />
      {customTestOutput && (
        <div className="px-4 pb-4">
          <TestOutputDisplay
            output={customTestOutput.output}
            expected={customTestOutput.expected}
            passed={customTestOutput.passed}
            isRunning={isCustomRunning}
            error={customTestOutput.error}
          />
        </div>
      )}
    </div>
  );
}
