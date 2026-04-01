from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud.analytics import get_correlation_insights, get_summary
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, CorrelationInsights

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        alias="from",
    ),
    date_to: date = Query(
        default_factory=date.today,
        alias="to",
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_summary(db, user.id, date_from, date_to)


@router.get("/insights", response_model=CorrelationInsights)
async def analytics_insights(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        alias="from",
    ),
    date_to: date = Query(
        default_factory=date.today,
        alias="to",
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_correlation_insights(db, user.id, date_from, date_to)
