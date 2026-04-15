# AIcodiingTeach 系统完善规格文档

> 本文档记录系统待完善功能的详细规格，供开发参考。

---

## 一、错题本系统

### 1.1 自动收集机制
- **触发条件**：用户在精进之路或挑战之路中答错的题目
- **收集内容**：
  - 题目ID、题目内容、用户答案、正确答案
  - 所属章节、知识点标签
  - 错误时间、错误次数（同一题多次错误累计）
- **去重逻辑**：同一题目多次错误只记录一次，但更新错误次数和最近错误时间

### 1.2 错题分析功能
- **知识点薄弱度分析**：根据错题统计各知识点的错误率
- **薄弱知识点排序**：按错误率从高到低排序
- **可视化展示**：雷达图/柱状图展示各知识点掌握情况

### 1.3 针对练习功能
- **练习生成**：根据薄弱知识点，AI生成针对性练习题
- **练习模式**：
  - 快速练习（5题）
  - 深度练习（10题）
  - 专项突破（选择特定知识点）
- **练习反馈**：完成后显示正确率变化趋势

### 1.4 复习提醒
- **艾宾浩斯遗忘曲线**：在关键时间点提醒复习（1天、3天、7天、15天、30天）
- **复习优先级**：根据错误次数和距离上次复习时间排序

---

## 二、收藏夹系统

### 2.1 收藏功能
- **收藏入口**：每道题旁边显示收藏按钮（星标图标）
- **收藏范围**：
  - 精进之路题目
  - 挑战之路题目
  - 错题本题目
- **收藏分类**：支持创建收藏夹分类（如"重点题"、"待复习"等）

### 2.2 收藏管理
- **收藏列表**：按收藏时间倒序排列
- **筛选功能**：按课程、章节、题目类型筛选
- **批量操作**：批量移动、批量删除

---

## 三、笔记系统

### 3.1 笔记创建
- **题目旁笔记**：每道题旁边有笔记按钮，点击创建该题相关笔记
- **独立笔记**：笔记页面可直接创建笔记
- **笔记关联**：可关联题目、知识点、章节

### 3.2 笔记编辑
- **富文本支持**：支持Markdown格式
- **代码高亮**：代码块支持语法高亮
- **图片上传**：支持上传图片

### 3.3 笔记管理
- **分类标签**：支持添加标签分类
- **搜索功能**：全文搜索笔记内容
- **导出功能**：导出为Markdown/PDF

---

## 四、打卡系统

### 4.1 打卡页面增强
- **农历显示**：显示农历日期
- **节气显示**：显示二十四节气（当日节气高亮）
- **节日显示**：显示传统节日
- **打卡统计**：连续打卡天数、总打卡天数

### 4.2 打卡激励
- **打卡奖励**：连续打卡获得经验值加成
- **打卡徽章**：特殊打卡成就（如"坚持30天"）

---

## 五、仪表盘统计

### 5.1 今日做题
- **统计范围**：仅统计挑战之路的题目
- **显示内容**：今日做题数量、今日正确率

### 5.2 学习时长
- **统计范围**：精进之路 + 挑战之路共同统计
- **显示内容**：今日学习时长、本周学习时长、总学习时长

### 5.3 知识点掌握度
- **计算方式**：基于该课程所有章节的测试正确率
- **可视化**：进度条/百分比显示
- **详情**：点击查看各章节掌握度明细

### 5.4 排行榜
- **范围**：针对单门课程
- **精进榜**：按经验值/掌握度排行
- **竞技榜**：按挑战积分排行

### 5.5 最近动态
- **动态类型**：
  - 精进之路：学习了某章节、完成了某章节测试
  - 挑战之路：完成了挑战、正确情况
- **显示格式**：
  - "学习了 C语言入门 - 变量与数据类型"
  - "完成挑战 难度3 正确率80%"
- **时间显示**：相对时间（如"5分钟前"）

---

## 六、精进之路改进

### 6.1 仪表盘卡片
- **卡片标题**：最近学习
- **显示内容**：
  - 最近学习的章节名称
  - 最近学习的小章节名称
  - 最近学习的知识点
  - 学习进度百分比
- **点击行为**：点击"开始学习"直接进入最近学习的章节

### 6.2 章节结构
```
课程
├── 大章节（如：C语言入门）
│   ├── 小章节（如：变量声明）
│   │   ├── 知识点1（如：整型变量）
│   │   ├── 知识点2（如：浮点型变量）
│   │   └── 知识点3（如：字符型变量）
│   ├── 小章节测试
│   └── 小章节掌握度评估
├── 大章节测试
└── 大章节掌握度评估
```

### 6.3 学习流程
1. 选择大章节 → 显示小章节列表
2. 选择小章节 → 显示知识点列表
3. 学习知识点 → 完成小章节测试
4. 小章节测试结果：
   - 全对：可选做提高题，标记小章节完成
   - 有错：针对错误知识点AI生成强化题，完成后标记小章节完成
5. 所有小章节完成 → 大章节综合测试
6. 大章节测试完成 → 计算章节掌握度

### 6.4 掌握度计算
- **小章节掌握度** = 小章节测试正确率 × 100%
- **大章节掌握度** = Σ(小章节掌握度) / 小章节数量 × 0.7 + 大章节测试正确率 × 0.3
- **课程掌握度** = Σ(大章节掌握度) / 大章节数量

### 6.5 AI助手组件（知识点浏览模式）
- **组件形态**：悬浮小圆球，可拖动
- **交互方式**：
  - 拖动到知识点附近：自动传递知识点上下文给AI
  - 直接点击：打开AI对话框，学生自由提问
- **额度限制**：无限制（知识点学习阶段）
- **上下文内容**：
  - 当前知识点标题、内容、代码示例
  - 相邻知识点信息（如拖动到某知识点附近）

### 6.6 经验值系统
- **获取方式**：
  - 完成小章节测试：+10 经验值
  - 完成大章节测试：+30 经验值
  - 全对奖励：额外 +10 经验值
- **用途**：精进榜排行

---

## 七、挑战之路改进

### 7.1 段位系统
```
青铜 → 白银 → 黄金 → 铂金 → 钻石 → 大师 → 王者
```
- **段位积分要求**：
  | 段位 | 所需积分 |
  |------|----------|
  | 青铜 | 0 |
  | 白银 | 1000 |
  | 黄金 | 3000 |
  | 铂金 | 6000 |
  | 钻石 | 10000 |
  | 大师 | 15000 |
  | 王者 | 25000 |

- **段位保护**：达到新段位后，积分掉落不会降段

### 7.2 仪表盘卡片
- **卡片标题**：挑战之路
- **显示内容**：
  - 当前段位（带图标）
  - 当前积分/下一段位积分
  - 最近练习的题目数量
- **点击行为**：点击"开始挑战"显示难度选择，选择后直接进入答题

### 7.3 难度系统
| 难度 | 基础积分 | AI额度奖励 | 题目特点 |
|------|----------|------------|----------|
| 1星 | 10 | 3 | 基础概念题 |
| 2星 | 20 | 5 | 基础应用题 |
| 3星 | 35 | 8 | 中等难度 |
| 4星 | 50 | 12 | 进阶题目 |
| 5星 | 70 | 18 | 困难题目 |

### 7.4 答题页面
- **AI辅助**：
  - 右侧显示AI助手面板
  - 可向AI提问获取提示
  - 每次提问消耗AI额度
- **时间限制**：无时间限制
- **题目类型**：根据用户画像生成，符合选定难度
- **代码编辑器**：Monaco Editor，支持语法高亮

### 7.5 积分奖励机制
- **基础积分**：根据难度获得基础积分
- **连对奖励**：
  | 连对次数 | 奖励倍率 |
  |----------|----------|
  | 2连对 | 1.2x |
  | 3连对 | 1.5x |
  | 5连对 | 2.0x |
  | 10连对 | 3.0x |
- **连续做题奖励**：
  - 每连续完成5题：额外 +10 积分
  - 每连续完成10题：额外 +30 积分

### 7.6 AI额度系统
- **初始额度**：每场挑战开始时，根据难度给予初始额度
- **获取方式**：完成每道题后获得额度奖励
- **消耗方式**：向AI提问消耗额度
- **额度不足**：显示提示，无法继续提问

### 7.7 用户画像
- **记录内容**：
  - 薄弱知识点
  - 擅长知识点
  - 常犯错误类型
  - 做题速度
- **应用场景**：
  - 生成符合用户水平的题目
  - 针对薄弱点增加相关题目出现概率

---

## 八、数据持久化

### 8.1 需持久化的数据
- 错题本记录
- 收藏夹数据
- 笔记数据
- 打卡记录
- 学习时长统计
- 知识点掌握度
- 段位和积分
- AI额度余额
- 用户画像数据
- 最近动态记录

### 8.2 数据同步
- **实时同步**：答题过程中实时保存进度
- **离线支持**：支持离线答题，联网后同步
- **数据备份**：定期备份用户学习数据

---

## 九、已确认方案

### Q1: 小章节与大章节的关系 ✅ 已确认
**决定方案**：新增 SubChapter 表，Chapter 包含多个 SubChapter
```
Course → Chapter(大章节) → SubChapter(小章节) → KnowledgePoint(知识点)
```
- 清晰的层级结构
- 便于后续扩展
- 每个小章节独立测试和评估

### Q2: 挑战之路题目来源 ✅ 已确认
**决定方案**：从现有题库筛选 + Hybrid Search 精准匹配

**推荐算法**：Hybrid Search（混合搜索）
- 结合 **向量相似度搜索** + **关键词搜索(BM25)**
- 使用 **RRF (Reciprocal Rank Fusion)** 算法融合排序
- 加上 **难度过滤** 作为过滤条件

实现逻辑：
```python
def search_exercises(user_profile, difficulty, course_id, limit):
    # 1. 向量搜索：基于用户画像/薄弱知识点
    vector_results = vector_search(
        query=user_profile.weak_points,
        course_id=course_id,
        limit=limit*2
    )
    
    # 2. 关键词搜索(BM25)：基于知识点标签
    keyword_results = bm25_search(
        query=user_profile.weak_points,
        course_id=course_id,
        limit=limit*2
    )
    
    # 3. RRF 融合
    fused_results = rrf_fusion(vector_results, keyword_results)
    
    # 4. 难度过滤
    final_results = filter_by_difficulty(fused_results, difficulty)
    
    return final_results[:limit]

def rrf_fusion(results1, results2, k=60):
    """RRF算法融合两个搜索结果"""
    scores = {}
    for rank, item in enumerate(results1):
        scores[item['id']] = scores.get(item['id'], 0) + 1/(k + rank + 1)
    for rank, item in enumerate(results2):
        scores[item['id']] = scores.get(item['id'], 0) + 1/(k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])
```

参考资料：
- [Weaviate Hybrid Search](https://weaviate.io/developers/weaviate/concepts/search/hybrid-search)
- [Azure AI Search: Hybrid Retrieval](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-ai-search-outperforming-vector-search-with-hybrid/ba-p/3929167)

### Q3: 连对奖励的计算时机 ✅ 已确认
**决定方案**：
- 同一用户、同一难度下累计连对
- 跨天累计，不跨难度
- 切换难度时重置连对计数

数据结构：
```sql
CREATE TABLE streak_record (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    course_id INTEGER NOT NULL,
    difficulty INTEGER NOT NULL,  -- 难度级别
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    last_correct_at DATETIME,
    UNIQUE(user_id, course_id, difficulty)  -- 每个用户每课程每难度独立记录
);
```

### Q4: AI助手上下文范围 ✅ 已确认
**决定方案**：精准模式 + 用户可选

交互设计：
1. **精准模式（默认）**：
   - 用户拖动AI到特定位置 → 传递当前句子/段落
   - 自动识别鼠标位置附近的文本内容
   
2. **知识点模式**：
   - 没有选中特定位置 → 传递当前知识点内容
   
3. **用户可选**：
   - 提供"选择上下文范围"按钮
   - 用户可手动选择：当前句子 / 当前段落 / 当前知识点 / 相邻知识点

技术实现：
```typescript
interface AIContext {
  mode: 'sentence' | 'paragraph' | 'knowledge_point' | 'custom';
  content: string;
  position?: {
    start: number;
    end: number;
  };
  relatedPoints?: string[];  // 相关知识点
}
```

### Q5: 段位降级机制 ✅ 已确认
**决定方案**：每周结算制 + 活跃保护

规则设计：
```
每周日自动结算：
1. 本周活跃（完成≥3场挑战）→ 段位保护（不掉段）
2. 本周不活跃 → 积分衰减 5%
3. 积分低于当前段位下限 → 降一段
4. 最低保持青铜段位
```

实现逻辑：
```python
async def weekly_rank_settlement():
    """每周段位结算"""
    users = await get_all_users()
    for user in users:
        # 检查本周活跃度
        weekly_challenges = await count_weekly_challenges(user.id)
        
        if weekly_challenges >= 3:
            # 活跃用户：段位保护
            continue
        
        # 不活跃用户：积分衰减
        user.points = int(user.points * 0.95)
        
        # 检查是否降段
        new_tier = calculate_tier(user.points)
        if new_tier != user.tier:
            user.tier = new_tier
            await notify_user(user.id, f"您的段位已调整为{new_tier}")
        
        await save_user(user)
```

段位保护机制的好处：
- 鼓励用户持续活跃
- 不会因偶尔做错题就掉段
- 保持竞争性但不至于太残酷

---

## 十、开发优先级建议

### P0（核心功能）
1. 错题本自动收集
2. 知识点掌握度计算
3. 段位系统
4. 挑战之路积分系统

### P1（重要功能）
1. 收藏夹功能
2. 笔记功能
3. AI额度系统
4. 连对奖励机制

### P2（增强功能）
1. 打卡农历/节气
2. 错题本针对练习
3. AI助手拖动交互
4. 用户画像应用

### P3（优化功能）
1. 复习提醒
2. 离线支持
3. 数据可视化
4. 导出功能

---

## 十一、技术实现要点

### 11.1 数据库新增表
```sql
-- 错题本
CREATE TABLE wrong_questions (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    question_id INTEGER NOT NULL,
    question_type VARCHAR NOT NULL,  -- 'base' / 'challenge'
    user_answer TEXT,
    correct_answer TEXT,
    error_count INTEGER DEFAULT 1,
    last_error_at DATETIME,
    created_at DATETIME
);

-- AI额度记录
CREATE TABLE ai_quota (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    total_quota INTEGER DEFAULT 0,
    used_quota INTEGER DEFAULT 0,
    updated_at DATETIME
);

-- 段位记录
CREATE TABLE user_rank (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    course_id INTEGER NOT NULL,
    tier VARCHAR DEFAULT 'bronze',  -- bronze/silver/gold/platinum/diamond/master/king
    points INTEGER DEFAULT 0,
    highest_tier VARCHAR DEFAULT 'bronze',
    updated_at DATETIME
);

-- 连对记录
CREATE TABLE streak_record (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    last_correct_at DATETIME
);
```

### 11.2 API端点规划
```
# 错题本
GET    /api/wrong-questions          # 获取错题列表
POST   /api/wrong-questions          # 添加错题（自动调用）
DELETE /api/wrong-questions/{id}     # 移除错题
GET    /api/wrong-questions/analysis # 获取错题分析
POST   /api/wrong-questions/practice # 生成针对练习

# 收藏夹
GET    /api/favorites                # 获取收藏列表
POST   /api/favorites                # 添加收藏
DELETE /api/favorites/{id}           # 取消收藏

# 笔记
GET    /api/notes                    # 获取笔记列表
POST   /api/notes                    # 创建笔记
PUT    /api/notes/{id}               # 更新笔记
DELETE /api/notes/{id}               # 删除笔记

# AI额度
GET    /api/ai-quota                 # 获取当前额度
POST   /api/ai-quota/use             # 消耗额度
POST   /api/ai-quota/earn            # 获取额度（内部调用）

# 段位
GET    /api/rank                     # 获取段位信息
GET    /api/rank/leaderboard         # 获取排行榜

# 连对
GET    /api/streak                   # 获取连对信息
POST   /api/streak/update            # 更新连对（内部调用）
```

---

*文档版本: v1.0*
*创建时间: 2026-04-15*
*状态: 待确认*
