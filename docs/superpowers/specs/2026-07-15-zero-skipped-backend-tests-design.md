# 后端零跳过测试修复设计

## 目标

消除后端测试套件中两个跳过项，并强化签到奖励的跨层契约，使测试结果达到 `555 passed, 0 skipped`。

## 范围

本次仅处理：

1. 每日签到返回值、用户智核余额和智核交易流水的一致性。
2. FPS XML 解析测试对仓库外样例文件的依赖。

不调整签到奖励算法、奖励数值、数据库结构或 FPS 解析器行为。

## 签到奖励契约

后端 `POST /api/users/checkin` 已通过 `CheckinResponse` 返回 `cores_earned`，服务层也已在同一数据库事务中更新用户余额并创建 `CoreTransaction`。现有跳过标记已经过期。

修复后的集成测试必须验证：

- 首次签到响应包含正数 `cores_earned`。
- 用户智核余额增量等于 `cores_earned`。
- 新增且仅新增一条 `category="checkin"`、`type="earn"` 的交易流水。
- 流水的 `amount` 等于 `cores_earned`，`balance_after` 等于签到后的用户余额。
- 同日重复签到返回 `cores_earned=0`，余额不再增加，也不新增签到流水。
- 前端 `CheckinResponse` 类型包含必填的 `cores_earned: number`，与后端响应模型保持一致。

任何一项数据库写入失败时，由现有请求级事务统一回滚，不在本次增加新的提交点。

## FPS 测试夹具

新增受版本控制的 `backend/tests/fixtures/sample_problems.xml`。样例采用最小但具有代表性的 FPS 结构，覆盖多题解析、标题、时间限制、内存限制和输入输出字段。

解析测试固定读取该夹具，不再读取被忽略的 `backend/data/`，也不再通过 `pytest.skip` 隐藏缺失文件。夹具缺失或解析结果错误都应使测试明确失败。

## 实施与验证

按 TDD 顺序实施：

1. 移除签到 skip 并强化断言，先确认当前契约测试的实际结果。
2. 增加重复签到与交易一致性断言。
3. 将 FPS 测试切换到尚不存在的新夹具路径，确认失败后添加夹具。
4. 补齐前端响应类型。
5. 运行后端完整测试，要求 `555 passed, 0 skipped`。
6. 运行前端完整测试、TypeScript 检查和生产构建。
7. 实际启动 FastAPI 与 Next.js，并确认后端健康响应和前端 `GET / 200`。

## 非目标

- 不清理其他 lint 警告。
- 不修改智核奖励阶梯。
- 不扩展 FPS 导入功能。
- 不引入新的兼容层或迁移脚本。
