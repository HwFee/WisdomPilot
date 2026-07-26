/**
 * API Module Index - 仅保留认证（其余旧 API 已随旧系统删除）
 */

export {
  login,
  register,
  getCurrentUser,
  forgotPassword,
  logout,
  getStoredUser,
  getStoredToken,
  isAuthenticated,
  type User,
  type Token,
} from "./auth";
