# Brainstorm Summary

- Change: refine-ai-teaching-system
- Date: 2026-06-17

## 确认的技术方案

采用“确定性教学主链路 + 受控 GAI 助教 + 挑战激励闭环”的系统定位。课程结构、题库、在线判题、进度、奖励、排行和统计由确定性服务负责；AI 只在分层提示、解析、代码反馈、可选反思追问和补救练习草稿等节点增强。

本 change 包含重构目标：拆分超长核心文件，尤其是 `backend/app/services/arena_infinite.py`、`backend/app/routers/learning_path.py` 和 `frontend/app/arena/_components/arena-content.tsx` 中的挑战路径相关职责。最终验证由当前会话的 reviewer 执行，不由另一个 AI 自行归档。

## 关键取舍与风险

- 不做全自动 AI 教学系统，避免 AI 题目质量、答案正确性和评分漂移风险。
- 不把 AI 输出作为闯关、奖励、排行的权威依据。
- 先写行为锁定测试，再拆服务，避免大文件重构造成隐性回归。
- 后端必须成为挑战提交权威判定方，前端测试结果只能作为展示或调试输入。
- 反思追问是可选增强，不能阻塞核心演示链路。

## 测试策略

- 后端 characterization tests 锁定挑战进度、切题、保存代码、追加题、提交奖励、错题收集等现有行为。
- 新增安全测试证明伪造客户端通过结果不能获得奖励或进度。
- AI 策略测试覆盖 hint cost、缓存复用、智核不足、general chat 分类。
- 前端测试覆盖 arena 提交流程和 API response shape。
- 最终验证包括 backend tests、frontend tests、frontend build、服务启动、受影响页面请求、CodeGraph sync/index。

## Spec Patch

无。OpenSpec delta specs 已在本 change 中创建：

- `controlled-ai-tutor`
- `challenge-path-architecture`
