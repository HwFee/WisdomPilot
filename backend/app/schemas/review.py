"""Review API Schemas - 复习相关数据传输对象"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class WeakPointBase(BaseModel):
    """Base weak point schema"""
    course_id: int
    knowledge_point: str
    error_count: int = 0
    mastery_level: int = Field(default=1, ge=1, le=5)


class WeakPointResponse(WeakPointBase):
    """Response for weak point"""
    id: str
    user_id: str
    last_error_at: Optional[datetime] = None
    review_count: int = 0
    last_review_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @property
    def weakness_score(self) -> float:
        """Calculate weakness score"""
        error_factor = min(1.0, self.error_count / 10)
        mastery_factor = (6 - self.mastery_level) / 5
        return (error_factor + mastery_factor) / 2


class SpacedRepetitionBase(BaseModel):
    """Base spaced repetition schema"""
    exercise_id: int
    stage_id: Optional[int] = None
    next_review_at: datetime
    review_interval: int = 1
    ease_factor: float = 2.5


class SpacedRepetitionResponse(SpacedRepetitionBase):
    """Response for spaced repetition record"""
    id: str
    user_id: str
    review_count: int = 0
    last_review_at: Optional[datetime] = None
    last_review_result: Optional[bool] = None

    model_config = {"from_attributes": True}

    @property
    def is_due(self) -> bool:
        """Check if review is due"""
        from app.utils.time import utc_now
        return utc_now() >= self.next_review_at

    @property
    def days_overdue(self) -> int:
        """Get days overdue"""
        from app.utils.time import utc_now
        from datetime import timedelta
        delta = utc_now() - self.next_review_at
        return max(0, delta.days)


class ReviewQueueItem(BaseModel):
    """Item in the review queue"""
    repetition: SpacedRepetitionResponse
    exercise_id: int
    exercise_type: str
    exercise_difficulty: int
    knowledge_points: List[str]
    stage_id: Optional[int] = None
    priority: float = 0.0  # Higher = more important to review

    model_config = {"from_attributes": True}


class ReviewQueueResponse(BaseModel):
    """Response for review queue endpoint"""
    items: List[ReviewQueueItem]
    total_due: int
    total_scheduled: int


class CompleteReviewRequest(BaseModel):
    """Request to complete a review"""
    exercise_id: int
    quality: int = Field(..., ge=0, le=5, description="Recall quality (0-5)")
    success: bool = Field(..., description="Whether the answer was correct")


class CompleteReviewResponse(BaseModel):
    """Response after completing a review"""
    repetition: SpacedRepetitionResponse
    weak_point_updated: bool = False
    mastery_change: int = 0
    message: str


class TargetPracticeRequest(BaseModel):
    """Request for targeted practice on weak points"""
    course_id: Optional[int] = None
    knowledge_points: Optional[List[str]] = None
    limit: int = Field(default=5, ge=1, le=20)


class TargetPracticeResponse(BaseModel):
    """Response with exercises for targeted practice"""
    exercises: List[dict]
    weak_points: List[WeakPointResponse]
    total: int


class WeakPointListResponse(BaseModel):
    """Response for weak points list endpoint"""
    weak_points: List[WeakPointResponse]
    total: int


class ReviewStatsResponse(BaseModel):
    """Response for review statistics"""
    total_due: int
    total_scheduled: int
    reviewed_today: int
    streak_days: int
    weak_points_count: int
    mastery_distribution: dict  # {level: count}


class WrongQuestionBase(BaseModel):
    """Base wrong question schema"""
    exercise_id: Optional[int] = None
    exercise_key: Optional[str] = None
    course_id: int
    chapter_id: Optional[int] = None
    knowledge_points: List[str]
    user_answer: Optional[Any] = None  # 可以是 dict 或 str
    correct_answer: Optional[Any] = None  # 可以是 dict 或 str
    exercise_type: str = "choice"
    exercise_difficulty: int = 1


class WrongQuestionResponse(WrongQuestionBase):
    """Response for wrong question"""
    id: str
    user_id: str
    error_count: int = 1
    is_resolved: bool = False
    first_error_at: datetime
    last_error_at: datetime
    resolved_at: Optional[datetime] = None
    exercise_content: Optional[dict] = None

    model_config = {"from_attributes": True}

    @property
    def days_since_last_error(self) -> int:
        """Days since last error"""
        from app.utils.time import utc_now
        delta = utc_now() - self.last_error_at
        return delta.days

    @property
    def priority_score(self) -> float:
        """Priority score for review"""
        error_factor = min(2.0, self.error_count / 5)
        unresolved_factor = 1.5 if not self.is_resolved else 0.5
        days_factor = min(1.0, self.days_since_last_error / 30)
        return error_factor * unresolved_factor * (1 + days_factor)

    @property
    def source_type(self) -> str:
        """题目来源类型: mastery(精进之路), arena(挑战之路), enhanced(强化测试)"""
        if not self.exercise_key:
            return "unknown"
        if self.exercise_key.startswith("mastery-"):
            return "mastery"
        elif self.exercise_key.startswith("arena-"):
            return "arena"
        elif self.exercise_key.startswith("enhanced-"):
            return "enhanced"
        return "unknown"

    @property
    def source_label(self) -> str:
        """题目来源中文标签"""
        labels = {
            "mastery": "精进之路",
            "arena": "挑战之路",
            "enhanced": "强化测试",
            "unknown": "未知来源"
        }
        return labels.get(self.source_type, "未知来源")

    @property
    def question_title(self) -> str:
        """题目标题/摘要"""
        if not self.exercise_content:
            return f"{self.exercise_type}题"
        # 尝试从 content 中提取标题
        if "title" in self.exercise_content:
            return self.exercise_content["title"]
        if "text" in self.exercise_content:
            text = self.exercise_content["text"]
            # 截取前50个字符作为标题
            if len(text) > 50:
                return text[:50] + "..."
            return text
        return f"{self.exercise_type}题"


class WrongQuestionListResponse(BaseModel):
    """Response for wrong questions list"""
    wrong_questions: List[WrongQuestionResponse]
    total: int
    unresolved_count: int


class WrongQuestionStatsResponse(BaseModel):
    """Response for wrong question statistics"""
    total: int
    resolved: int
    unresolved: int
    total_errors: int
    mastery_distribution: dict  # {knowledge_point: {error_count, mastery_level, weak_score}}


class KnowledgePointAnalysis(BaseModel):
    """Analysis for a single knowledge point"""
    knowledge_point: str
    error_count: int
    total_attempts: int
    error_rate: float  # 0.0 - 1.0
    mastery_level: int  # 1-5
    weak_score: float  # 0.0 - 1.0 (higher = weaker)
    rank: int  # Ranking by weakness (1 = weakest)


class WeakPointAnalysisResponse(BaseModel):
    """Response for weak point analysis"""
    knowledge_points: List[KnowledgePointAnalysis]
    weakest_knowledge_points: List[KnowledgePointAnalysis]  # Top 5
    strongest_knowledge_points: List[KnowledgePointAnalysis]  # Top 5
    total_knowledge_points: int
    overall_error_rate: float


class TargetPracticeMode(str):
    """Practice mode types"""
    QUICK = "quick"  # 5 questions
    DEEP = "deep"  # 10 questions
    SPECIFIC = "specific"  # Specific knowledge points


class EnhancedTargetPracticeRequest(BaseModel):
    """Enhanced request for targeted practice"""
    course_id: Optional[int] = None
    mode: str = Field(default="quick", description="quick, deep, or specific")
    knowledge_points: Optional[List[str]] = None
    difficulty_range: Optional[tuple[int, int]] = None
    limit: int = Field(default=5, ge=1, le=20)

    model_config = {"arbitrary_types_allowed": True}


class EnhancedTargetPracticeResponse(BaseModel):
    """Enhanced response with exercises for targeted practice"""
    exercises: List[dict]
    weak_points: List[WeakPointResponse]
    mode: str
    total: int
    message: str


class ReviewReminderResponse(BaseModel):
    """Response for review reminders based on Ebbinghaus curve"""
    due_reviews: List[ReviewQueueItem]
    upcoming_reviews: List[dict]  # {date: str, count: int}
    ebbinghaus_schedule: List[dict]  # {day: int, label: str, count: int}
    total_due: int
    total_upcoming: int


class CollectWrongQuestionRequest(BaseModel):
    """Request to collect a wrong question (for frontend hardcoded exercises)"""
    exercise_key: str = Field(..., description="练习题标识，格式：chapterId-subsectionIndex-exerciseId")
    user_answer: Any = Field(..., description="用户答案")
    course_id: int = Field(..., description="课程ID")
    chapter_id: Optional[int] = Field(None, description="章节ID")
    exercise_content: Optional[dict] = Field(None, description="题目内容快照")
    exercise_type: str = Field(default="choice", description="题目类型")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")


class CollectWrongQuestionResponse(BaseModel):
    """Response after collecting a wrong question"""
    id: str
    exercise_key: str
    error_count: int
    is_resolved: bool
    message: str
