/**
 * Tests for dashboard detail pages
 */

import { render, screen, waitFor, act } from "@testing-library/react";

// Mock next/navigation
const mockPush = jest.fn();
const mockBack = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
  }),
}));

// Mock API functions
jest.mock("@/lib/api", () => ({
  getStoredToken: () => "test-token",
  logout: jest.fn(),
  getExercisesTrend: jest.fn().mockResolvedValue({
    trends: [
      { date: "2024-01-15", count: 10 },
      { date: "2024-01-14", count: 8 },
    ],
  }),
  getAccuracyTrend: jest.fn().mockResolvedValue({
    trends: [{ date: "2024-01-15", accuracy: 85, total: 10, correct: 8 }],
  }),
  getTimeTrend: jest.fn().mockResolvedValue({
    trends: [{ date: "2024-01-15", minutes: 45 }],
  }),
  getFavorites: jest.fn().mockResolvedValue({
    favorites: [],
    total: 0,
  }),
  getNotes: jest.fn().mockResolvedValue({
    notes: [],
    total: 0,
  }),
}));

// Import pages after mocking
import ExercisesPage from "@/app/dashboard/exercises/page";
import AccuracyPage from "@/app/dashboard/accuracy/page";
import TimePage from "@/app/dashboard/time/page";
import FavoritesPage from "@/app/favorites/page";

describe("Dashboard Detail Pages", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Exercises Detail Page", () => {
    it("renders loading state initially", async () => {
      render(<ExercisesPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
      // Flush all pending async state updates to avoid act() warnings
      await act(async () => {});
    });

    it("renders content after loading", async () => {
      render(<ExercisesPage />);
      await waitFor(() => {
        expect(
          screen.getByText("今日做题详情（挑战之路）"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Accuracy Detail Page", () => {
    it("renders loading state initially", async () => {
      render(<AccuracyPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
      // Flush all pending async state updates to avoid act() warnings
      await act(async () => {});
    });

    it("renders content after loading", async () => {
      render(<AccuracyPage />);
      await waitFor(() => {
        expect(screen.getByText("正确率详情（挑战之路）")).toBeInTheDocument();
      });
    });
  });

  describe("Time Detail Page", () => {
    it("renders loading state initially", async () => {
      render(<TimePage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
      // Flush all pending async state updates to avoid act() warnings
      await act(async () => {});
    });

    it("renders content after loading", async () => {
      render(<TimePage />);
      await waitFor(() => {
        expect(
          screen.getByText("学习时长详情（精进之路 + 挑战之路）"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Favorites Page", () => {
    it("renders favorites page without crashing", async () => {
      render(<FavoritesPage />);
      // FavoritesPage renders immediately with mock data (no transient loading state)
      expect(document.body).toBeTruthy();
      // Flush any pending async updates
      await act(async () => {});
    });

    it("renders empty state when no favorites", async () => {
      render(<FavoritesPage />);
      await waitFor(() => {
        expect(screen.getByText("暂无收藏")).toBeInTheDocument();
      });
    });
  });
});
