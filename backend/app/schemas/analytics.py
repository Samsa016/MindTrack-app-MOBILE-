from datetime import date, datetime

from pydantic import BaseModel


class MoodTrendPoint(BaseModel):
    date: date
    mood_score: int
    stress_score: int
    sleep_hours: float
    sentiment_score: float | None = None


class TagCount(BaseModel):
    tag: str
    count: int


class AnalyticsSummary(BaseModel):
    period_from: date
    period_to: date
    total_entries: int
    avg_mood: float
    avg_stress: float
    avg_sleep: float
    mood_trend: list[MoodTrendPoint]
    top_tags: list[TagCount]
    sentiment_avg: float | None


class CorrelationMetrics(BaseModel):
    avg_sleep_with_tag: float | None = None
    avg_sleep_without_tag: float | None = None
    avg_stress_with_tag: float | None = None
    avg_stress_without_tag: float | None = None
    avg_mood_with_tag: float | None = None
    avg_mood_without_tag: float | None = None


class InsightItem(BaseModel):
    type: str  # "tag_correlation" | "trend"
    tag: str | None = None
    description: str
    metrics: CorrelationMetrics | None = None


class CorrelationInsights(BaseModel):
    insights: list[InsightItem]
    generated_at: datetime
