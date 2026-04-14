# 关卡完成持久化与功能完善计划

## 问题分析

用户完成第一道编程题后，以下数据没有正确持久化/更新：

1. **经验值 (XP)** - 仅在前端本地状态计算，未实际保存到用户表
2. **关卡进度** - `completePractice` API 只更新练习计数，但缺少完整的进度追踪
3. **学习进度** - 章节掌握度未更新
4. **排行榜** - 数据未同步更新

另外缺失的功能：
1. **知识点验证弹窗** - 完成编程题后应弹出选择题验证知识点
2. **IDE 界面美化** - 当前纯黑白太复古

---

## Phase 1: 修复数据持久化问题

### 1.1 后端：完善 `completePractice` API

**问题**: 当前 `completePractice` 只更新练习计数，没有：
- 累计经验值
- 更新用户学习统计
- 触发排行榜更新

**修改**: `backend/app/routers/stages.py`

```python
@router.post("/{stage_id}/complete", response_model=CompletePracticeResponse)
async def complete_practice(...):
    # ... 现有逻辑 ...
    
    # 新增：计算并奖励 XP（每道题正确奖励部分 XP）
    if request.exercises_correct > request.exercises_completed * 0:
        xp_per_exercise = stage.xp_reward // stage.required_exercises
        earned_xp = xp_per_exercise * request.exercises_correct
        user.xp = (user.xp or 0) + earned_xp
        user.total_xp = (user.total_xp or 0) + earned_xp
    
    # 新增：更新用户学习统计
    user.total_exercises = (user.total_exercises or 0) + request.exercises_completed
    user.correct_exercises = (user.correct_exercises or 0) + request.exercises_correct
    
    await db.commit()  # 确保提交
```

### 1.2 后端：完善 `submitVerification` API

**问题**: 验证通过后，经验值和配额更新了，但缺少：
- 章节掌握度更新
- 排行榜数据同步
- 成就检查

**修改**: `backend/app/routers/stages.py`

```python
if passed:
    # ... 现有逻辑 ...
    
    # 新增：更新章节掌握度
    if stage.chapter_id:
        await update_chapter_mastery(db, user.id, stage.chapter_id)
    
    # 新增：更新排行榜
    await update_leaderboard(db, user.id, stage.course_id)
    
    # 新增：检查成就
    await check_achievements(db, user)
```

### 1.3 新增：更新章节掌握度的服务

**文件**: `backend/app/services/mastery.py`

```python
async def update_chapter_mastery(db, user_id, chapter_id):
    """更新用户章节掌握度"""
    # 获取章节所有关卡
    # 计算完成率和正确率
    # 更新 ChapterMastery 表
```

### 1.4 前端：刷新用户数据

**问题**: 完成题目后前端状态未刷新

**修改**: `frontend/app/stage/[id]/page.tsx`

```typescript
// 完成题目后刷新用户数据
import { useUser } from '@/hooks/useUser'

// 在 completePractice 成功后
const { refreshUser } = useUser()
await refreshUser()
```

---

## Phase 2: 知识点验证弹窗

### 2.1 后端：生成知识点验证题

**新增端点**: `POST /api/stages/{stage_id}/knowledge-check`

```python
@router.post("/{stage_id}/knowledge-check")
async def get_knowledge_check(...):
    """生成知识点验证选择题"""
    # 获取关卡学习目标
    # 使用 AI 生成 2-3 道选择题
    # 返回题目列表
```

### 2.2 前端：知识点验证弹窗组件

**新增组件**: `frontend/components/stage/KnowledgeCheckModal.tsx`

```tsx
// 在完成练习题后弹出
// 显示 2-3 道选择题
// 验证用户是否理解核心概念
// 通过后才能进入验证阶段
```

### 2.3 集成流程

```
用户完成练习题 
  → 弹出知识点验证弹窗 
  → 用户答对 70% 以上 
  → 解锁验证阶段按钮
```

---

## Phase 3: IDE 界面美化

### 3.1 配色方案升级

当前问题：纯黑白配色太单调

改进方向：
- 渐变背景（深蓝到紫色）
- 语法高亮增强
- 按钮渐变色
- 状态指示器动画

### 3.2 组件改进

**问题面板 (左侧 40%)**:
- 添加卡片阴影和圆角
- 难度标签使用彩色渐变
- 知识点标签使用胶囊样式

**代码编辑器 (右侧 60%)**:
- Monaco 编辑器主题优化
- 行号区域美化
- 光标高亮行

**底部操作栏**:
- 渐变背景
- 进度条动画
- 成功/失败状态动画

---

## 实施顺序

1. **Phase 1.1-1.2** - 修复后端持久化 (30分钟)
2. **Phase 1.3-1.4** - 添加掌握度服务和前端刷新 (30分钟)
3. **Phase 2.1-2.3** - 知识点验证弹窗 (1小时)
4. **Phase 3.1-3.2** - IDE 界面美化 (1小时)

---

## 涉及文件

**后端修改**:
- `backend/app/routers/stages.py` - 完善持久化逻辑
- `backend/app/services/mastery.py` - 新增掌握度服务
- `backend/app/schemas/stage.py` - 新增知识点验证 schema

**前端修改**:
- `frontend/app/stage/[id]/page.tsx` - 集成刷新和弹窗
- `frontend/components/stage/KnowledgeCheckModal.tsx` - 新增弹窗组件
- `frontend/hooks/useUser.ts` - 添加刷新用户数据方法
- `frontend/app/globals.css` - 美化样式
