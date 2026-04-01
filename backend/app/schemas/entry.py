from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EntryCreate(BaseModel):
    mood_score: int = Field(..., ge=1, le=10, description="Mood 1-10")
    stress_score: int = Field(..., ge=1, le=10, description="Stress 1-10")
    sleep_hours: float = Field(..., ge=0, le=24, description="Sleep 0-24h")
    note_text: str | None = Field(None, max_length=5000)
    entry_date: date


class EntryUpdate(BaseModel):
    mood_score: int | None = Field(None, ge=1, le=10)
    stress_score: int | None = Field(None, ge=1, le=10)
    sleep_hours: float | None = Field(None, ge=0, le=24)
    note_text: str | None = Field(None, max_length=5000)


class AIAnalysisResponse(BaseModel):
    sentiment_score: float
    extracted_tags: list[str]
    insight: str | None

    model_config = {"from_attributes": True}


class EntryResponse(BaseModel):
    id: UUID
    mood_score: int
    stress_score: int
    sleep_hours: float
    note_text: str | None
    entry_date: date
    ai_status: str
    ai_analysis: AIAnalysisResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntryListResponse(BaseModel):
    items: list[EntryResponse]
    total: int
