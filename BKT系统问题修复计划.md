# BKT 掌握度系统问题修复计划

## 当前发现的所有问题

### 问题 1: 路由结构错误（严重）

**现状**：
```
/mastery/[courseId]/section/[sectionId]  ← 缺少 chapter 信息
```

**应该**：
```
/mastery/[courseId]/chapter/[chapterId]/section/[sectionId]
```

**影响**：
- 无法知道小节属于哪个章节
- 小节学习页面无法正确关联章节信息
- BKT 更新时无法传递 `chapter_id` 和 `section_id`

**修复步骤**：
1. 移动 `section/[sectionId]` 目录到 `chapter/[chapterId]/section/[sectionId]`
2. 更新所有跳转链接
3. 更新小节学习页面的路由参数获取逻辑

---

### 问题 2: BKT 小节掌握度聚合逻辑错误（严重）

**现状**：
- `KnowledgePointMastery` 没有关联到具体小节
- `_update_section_mastery` 用 `chapter_id` 过滤知识点
- 导致：做一道题影响整个章节所有小节的掌握度

**已修复**：
- ✅ 添加 `section_id` 字段到 `KnowledgePointMastery`
- ✅ 修改 `_update_section_mastery` 使用 `section_id` 过滤
- ✅ 数据库迁移添加 `section_id` 列

**待修复**：
- ❌ `save_exercise_progress` 没有传递 `section_id` 给 BKT 服务
- ❌ 前端 API 调用没有传 `section_id`

---

### 问题 3: 前端没有传递 section_id（严重）

**现状**：
- `MasteryExerciseProgressSaveRequest` 已添加 `section_id` 字段
- 但前端调用 `saveMasteryExerciseProgress` 时没有传值

**修复步骤**：
1. 小节学习页面跳转到做题页面时，存储当前 `sectionId`
2. 做题页面从 URL 或 localStorage 获取 `sectionId`
3. 调用 API 时传递 `section_id`

---

### 问题 4: UI 显示混乱（中等）

**用户反馈**：
- 章节掌握度 26%，但显示"入门"（应该是"学习"）
- 小节掌握度没有在列表中显示
- 做一题后章节掌握度涨太多

**原因分析**：
- 掌握度等级划分可能有问题
- 小节列表 API 返回的 `mastery_score` 可能为 null
- BKT 聚合逻辑导致掌握度计算不准确

**修复步骤**：
1. 检查 `getMasteryLevel` 函数的阈值设置
2. 确保小节 API 正确返回 `mastery_score`
3. 修复 BKT 聚合后确保掌握度正确计算

---

### 问题 5: 主页面逻辑混乱（中等）

**现状**：
- `/mastery/[courseId]/page.tsx` 同时包含：
  - 章节选择逻辑
  - 答题逻辑（base_quiz, enhanced_quiz）
  - 分析逻辑
  - 结果逻辑

**问题**：
- 代码量过大（2000+ 行）
- 职责不清晰
- 答题应该在章节/小节页面进行，不应该在主页

**建议**：
- 主页面只负责章节选择
- 答题逻辑移到小节学习页面
- 或者重构为独立组件

---

## 修复优先级

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 | 路由结构错误 | 核心功能无法正常工作 |
| P0 | BKT section_id 未传递 | 小节掌握度无法正确计算 |
| P1 | 前端未传 section_id | 后端无法关联小节 |
| P1 | UI 显示混乱 | 用户体验差 |
| P2 | 主页面逻辑混乱 | 代码可维护性差 |

---

## 详细修复步骤

### Phase 1: 修复路由结构（P0）

```bash
# 1. 创建新的目录结构
mkdir -p frontend/app/mastery/[courseId]/chapter/[chapterId]/section/[sectionId]

# 2. 移动小节学习页面
mv frontend/app/mastery/[courseId]/section/[sectionId]/page.tsx \
   frontend/app/mastery/[courseId]/chapter/[chapterId]/section/[sectionId]/page.tsx

# 3. 删除旧目录
rm -rf frontend/app/mastery/[courseId]/section
```

**需要更新的跳转链接**：
- 小节选择页面 → 小节学习页面
- 小节学习页面 → 返回小节选择
- 小节学习页面 → 做题页面

### Phase 2: 修复 BKT section_id 传递（P0）

**后端修改**：
1. `mastery_progress.py` - `save_exercise_progress`:
```python
bkt_result = await bkt_service.process_answer(
    user_id=user_id,
    question_source="mastery",
    question_id=request.question_id,
    is_correct=request.is_correct,
    knowledge_points=knowledge_points,
    course_id=request.course_id,
    chapter_id=request.chapter_id,
    section_id=request.section_id,  # 添加这行
    difficulty=difficulty,
    question_type=request.question_type,
    user_answer=request.user_answer,
)
```

**前端修改**：
1. 小节学习页面存储当前 sectionId
2. 做题时从存储中获取并传递

### Phase 3: 修复 UI 显示（P1）

1. 检查掌握度等级阈值：
```typescript
function getMasteryLevel(score: number) {
  if (score >= 95) return '精通'
  if (score >= 85) return '熟练'
  if (score >= 70) return '练习'
  if (score >= 50) return '学习'  // 26% 应该是 '入门'，不是 '学习'
  return '入门'
}
```

2. 确保小节 API 返回 mastery_score

### Phase 4: 清理主页面逻辑（P2）

- 将答题相关逻辑提取为独立组件
- 或移到小节学习页面

---

## 验证步骤

修复完成后，按以下步骤验证：

1. **路由验证**：
   - 访问 `/mastery/1/chapter/1` → 应显示小节列表
   - 点击小节 → URL 应为 `/mastery/1/chapter/1/section/1`

2. **BKT 验证**：
   - 在小节 1 做题 → 只影响小节 1 的掌握度
   - 小节 2 的掌握度应该不变
   - 章节掌握度 = 所有小节的平均值

3. **UI 验证**：
   - 小节列表显示各小节的掌握度
   - 掌握度等级与数值匹配
   - 做题后掌握度正确更新

---

## 时间估算

| 阶段 | 时间 |
|------|------|
| Phase 1: 路由结构 | 30 分钟 |
| Phase 2: BKT section_id | 30 分钟 |
| Phase 3: UI 显示 | 20 分钟 |
| Phase 4: 主页面清理 | 1 小时（可选） |
| **总计** | **2-3 小时** |
