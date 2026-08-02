from typing import Literal
from pydantic import BaseModel, Field


class DashboardTask(BaseModel):
    id: int
    title: str
    task_type: str
    target_count: int
    completed_count: int
    estimated_minutes: int
    status: str


class DashboardResponse(BaseModel):
    plan_name: str
    target_completion_date: str
    days_remaining: int
    progress_percent: float
    streak_days: int
    tasks: list[DashboardTask]


class EvidenceItem(BaseModel):
    text: str
    translation: str


class VocabularyItem(BaseModel):
    word: str
    meaning: str


class FollowUpQuestion(BaseModel):
    question: str
    answer: str
    explanation: str


class AiExplanation(BaseModel):
    summary: str
    correct_reason: str
    wrong_reason: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    vocabulary: list[VocabularyItem] = Field(default_factory=list)
    grammar: list[str] = Field(default_factory=list)
    strategy: str
    follow_up_question: FollowUpQuestion | None = None


class ExplainMistakeRequest(BaseModel):
    question_id: int | None = None
    question_type: str
    passage: str = ""
    question: str
    options: dict[str, str] = Field(default_factory=dict)
    user_answer: str
    correct_answer: str
    official_explanation: str = ""
    error_reason: str = ""
    model: Literal["deepseek-v4-flash", "deepseek-v4-pro"] | None = None
    regenerate: bool = False


class ExplainMistakeResponse(BaseModel):
    explanation: AiExplanation
    model: str
    cached: bool


class AiStatusResponse(BaseModel):
    configured: bool
    default_model: str
    base_url: str


class AiSettingsUpdate(BaseModel):
    api_key: str | None = None
    model: Literal["deepseek-v4-flash", "deepseek-v4-pro"]


class WordCard(BaseModel):
    id: int
    word: str
    phonetic: str | None = None
    meaning: str
    part_of_speech: str | None = None
    example: str | None = None
    example_translation: str | None = None
    status: str
    review_count: int


class WordSessionResponse(BaseModel):
    words: list[WordCard]
    review_count: int
    new_count: int


class WordReviewRequest(BaseModel):
    result: Literal["unknown", "fuzzy", "known"]
    response_seconds: int | None = Field(default=None, ge=0)


class WordReviewResponse(BaseModel):
    word_id: int
    status: str
    familiarity: float
    interval_days: int
    next_review_at: str


class LessonSection(BaseModel):
    id: int
    section_type: str
    title: str
    content: str
    translation: str


class LessonVocabulary(BaseModel):
    word: str
    phonetic: str | None = None
    part_of_speech: str | None = None
    meaning: str
    example: str
    example_translation: str


class LessonQuestion(BaseModel):
    id: int
    question: str
    options: dict[str, str]
    correct_answer: str
    explanation: str


class LessonResponse(BaseModel):
    id: int
    unit_number: int
    lesson_number: int
    title: str
    subtitle: str
    level: str
    objectives: list[str]
    estimated_minutes: int
    completed: bool
    score: int | None = None
    sections: list[LessonSection]
    vocabulary: list[LessonVocabulary]
    questions: list[LessonQuestion]


class LessonCompleteRequest(BaseModel):
    answers: dict[str, str]


class LessonCompleteResponse(BaseModel):
    lesson_id: int
    score: int
    correct_count: int
    question_count: int
    completed: bool
