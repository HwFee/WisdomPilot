# 删库重建指南（无数据迁移）

> 日期：2026-07-26
> 关键决策：**存量数据全部清零，含账号。不做任何字段级迁移。**

## 为什么不做迁移

旧系统的学习数据（XP、段位、错题、章节进度、BKT 掌握度）全部绑定在已废弃的玩法上，
且自身质量不可信（AI 生成的习题/知识点是这次重塑的直接原因）。把这些数据搬进新体系
只会污染三根能力轴。新账号体系字段也从简重建，没有保留旧 users 行的价值。

## 步骤

1. **备份**（仅作灾难回滚，不作迁移源）：
   ```bash
   cp backend/data.db backend/data.db.backup-$(date +%Y%m%d)
   ```
2. **停服 → 删库 → 重建**：
   ```bash
   # 停止后端后
   rm backend/data.db backend/data.db-shm backend/data.db-wal
   # 用 01-target-design.md 第 8 节的表结构重建（Alembic upgrade head 或建表脚本）
   ```
3. **灌入种子数据**（新系统运行所必需，全部来自内容团队/脚本，不来自旧库）：
   - `knowledge_points`：初始 ~15 个知识点，按三轴分组
   - `review_sessions` + `injected_defects`：首批 ≥10 关，每关缺陷经人工复核
   - `arena_challenges`：首批 ≥7 个（支持每日轮换）
   - `cert_exams` + `cert_questions`：定级测试 1 套 + 认证 ≥3 套
   - 脚本命名建议 `backend/scripts/seed_*.py`，可重复执行（幂等：先清后插）。
4. **冒烟验证**：注册新账号 → 定级测试 → /api/dashboard 返回非空 main_task → 四模块各跑通一次。

## 回滚

回滚 = 停服 + 用 `data.db.backup-*` 覆盖回 `data.db` + 切回旧代码。
新库不做向后兼容，回滚即放弃新数据（重建初期用户量小，可接受）。

## 旧文档说明

本文件此前的「字段级迁移方案」已作废删除——那是在「保留学习数据」决策下写的，
该决策已被推翻（见 `docs/superpowers/specs/2026-07-26-deck-rebuild-design.md` 第 0 节）。
