import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # AI-generated fields
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    extracted_tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    insight: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="ai_analysis")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AIAnalysis entry={self.entry_id} sentiment={self.sentiment_score}>"
