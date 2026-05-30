/**
 * @jest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { TodayStats } from "../TodayStats";

describe("TodayStats", () => {
  const mockStats = {
    exercisesToday: 10,
    accuracy: 85,
    learningMinutes: 45,
    streakDays: 7,
  };

  const mockTrend = {
    exercises: 5,
    accuracy: 3,
    time: -10,
  };

  it("renders all 4 stat cards", () => {
    render(<TodayStats stats={mockStats} />);

    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("45分钟")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("displays correct labels in Chinese", () => {
    render(<TodayStats stats={mockStats} lang="zh" />);

    expect(screen.getByText("今日做题（挑战之路）")).toBeInTheDocument();
    expect(screen.getByText("正确率（挑战之路）")).toBeInTheDocument();
    expect(screen.getByText("学习时长（双路径总计）")).toBeInTheDocument();
    expect(screen.getByText("连续打卡")).toBeInTheDocument();
  });

  it("displays correct labels in English", () => {
    render(<TodayStats stats={mockStats} lang="en" />);

    expect(screen.getByText("Exercises (Challenge Path)")).toBeInTheDocument();
    expect(screen.getByText("Accuracy (Challenge Path)")).toBeInTheDocument();
    expect(screen.getByText("Time (All Paths)")).toBeInTheDocument();
    expect(screen.getByText("Streak")).toBeInTheDocument();
  });

  it("shows trend indicators when provided", () => {
    render(<TodayStats stats={mockStats} trend={mockTrend} />);

    expect(screen.getByText("+5%")).toBeInTheDocument();
    expect(screen.getByText("+3%")).toBeInTheDocument();
    expect(screen.getByText("-10%")).toBeInTheDocument();
  });

  it("shows guide text when stats are zero", () => {
    const zeroStats = {
      exercisesToday: 0,
      accuracy: 0,
      learningMinutes: 0,
      streakDays: 0,
    };
    render(<TodayStats stats={zeroStats} lang="zh" />);

    expect(screen.getByText("目标：10题 →")).toBeInTheDocument();
    expect(screen.getByText("保持专注 →")).toBeInTheDocument();
  });

  it("renders 4 equal-width cards in grid", () => {
    const { container } = render(<TodayStats stats={mockStats} />);
    const grid = container.querySelector('[class*="grid-cols-4"]');
    expect(grid).toBeInTheDocument();
  });
});
