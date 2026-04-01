from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entry import AIStatus, Entry
from app.models.ai_analysis import AIAnalysis
from app.schemas.entry import EntryCreate, EntryUpdate


async def create_entry(
    db: AsyncSession,
    user_id: UUID,
    payload: EntryCreate,
) -> Entry:
    entry = Entry(
        user_id=user_id,
        mood_score=payload.mood_score,
        stress_score=payload.stress_score,
        sleep_hours=payload.sleep_hours,
        note_text=payload.note_text,
        entry_date=payload.entry_date,
        ai_status=AIStatus.PENDING,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry, attribute_names=["ai_analysis"])
    return entry


async def get_entry(
    db: AsyncSession,
    entry_id: UUID,
    user_id: UUID,
) -> Entry | None:
    stmt = (
        select(Entry)
        .options(selectinload(Entry.ai_analysis))
        .where(Entry.id == entry_id, Entry.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_entries(
    db: AsyncSession,
    user_id: UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 30,
    offset: int = 0,
) -> tuple[list[Entry], int]:
    base = select(Entry).where(Entry.user_id == user_id)

    if date_from:
        base = base.where(Entry.entry_date >= date_from)
    if date_to:
        base = base.where(Entry.entry_date <= date_to)

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Items
    stmt = (
        base.options(selectinload(Entry.ai_analysis))
        .order_by(Entry.entry_date.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def update_entry(
    db: AsyncSession,
    entry: Entry,
    payload: EntryUpdate,
) -> Entry:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    # Re-trigger AI analysis if text was updated
    if "note_text" in update_data and update_data["note_text"]:
        entry.ai_status = AIStatus.PENDING
        # Delete old analysis if exists
        if entry.ai_analysis:
            await db.delete(entry.ai_analysis)

    await db.flush()
    await db.refresh(entry, attribute_names=["ai_analysis"])
    return entry


async def delete_entry(db: AsyncSession, entry: Entry) -> None:
    await db.delete(entry)
    await db.flush()


async def save_ai_analysis(
    db: AsyncSession,
    entry_id: UUID,
    sentiment_score: float,
    extracted_tags: list[str],
    insight: str | None,
    model_name: str | None,
    processing_time_ms: int | None,
) -> None:
    """Save AI analysis results and update entry status."""
    # Get entry
    entry = await db.get(Entry, entry_id)
    if not entry:
        return

    # Create or update analysis
    analysis = AIAnalysis(
        entry_id=entry_id,
        sentiment_score=sentiment_score,
        extracted_tags=extracted_tags,
        insight=insight,
        model_name=model_name,
        processing_time_ms=processing_time_ms,
    )
    db.add(analysis)
    entry.ai_status = AIStatus.DONE
    await db.flush()
