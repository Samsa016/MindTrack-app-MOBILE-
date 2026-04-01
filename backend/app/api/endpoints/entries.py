from datetime import date
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud.entry import (
    create_entry,
    delete_entry,
    get_entries,
    get_entry,
    update_entry,
)
from app.models.user import User
from app.schemas.entry import EntryCreate, EntryListResponse, EntryResponse, EntryUpdate
from app.services.ai_service import analyze_entry_background

router = APIRouter()


@router.post(
    "",
    response_model=EntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry_endpoint(
    payload: EntryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a daily check-in entry. Returns immediately, AI processes in background."""
    entry = await create_entry(db, user.id, payload)

    # Trigger background AI analysis if there's text to analyze
    if payload.note_text and payload.note_text.strip():
        background_tasks.add_task(
            analyze_entry_background,
            entry_id=entry.id,
            note_text=payload.note_text,
            mood_score=payload.mood_score,
            stress_score=payload.stress_score,
            sleep_hours=payload.sleep_hours,
        )

    return EntryResponse.model_validate(entry)


@router.get("", response_model=EntryListResponse)
async def list_entries(
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = await get_entries(db, user.id, date_from, date_to, limit, offset)
    return EntryListResponse(
        items=[EntryResponse.model_validate(e) for e in items],
        total=total,
    )


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry_endpoint(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = await get_entry(db, entry_id, user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )
    return EntryResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry_endpoint(
    entry_id: UUID,
    payload: EntryUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = await get_entry(db, entry_id, user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    updated = await update_entry(db, entry, payload)

    # Re-trigger AI if text changed
    if payload.note_text and payload.note_text.strip():
        background_tasks.add_task(
            analyze_entry_background,
            entry_id=updated.id,
            note_text=payload.note_text,
            mood_score=updated.mood_score,
            stress_score=updated.stress_score,
            sleep_hours=updated.sleep_hours,
        )

    return EntryResponse.model_validate(updated)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry_endpoint(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = await get_entry(db, entry_id, user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )
    await delete_entry(db, entry)
