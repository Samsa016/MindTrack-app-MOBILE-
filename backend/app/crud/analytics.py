from collections import Counter
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.models.entry import AIStatus, Entry
from app.schemas.analytics import (
    AnalyticsSummary,
    CorrelationInsights,
    CorrelationMetrics,
    InsightItem,
    MoodTrendPoint,
    TagCount,
)


async def get_summary(
    db: AsyncSession,
    user_id: UUID,
    date_from: date,
    date_to: date,
) -> AnalyticsSummary:
    """Aggregate entry metrics for the given period."""
    base = select(Entry).where(
        Entry.user_id == user_id,
        Entry.entry_date >= date_from,
        Entry.entry_date <= date_to,
    )

    # Aggregates
    agg_stmt = select(
        func.count(Entry.id).label("total"),
        func.avg(Entry.mood_score).label("avg_mood"),
        func.avg(Entry.stress_score).label("avg_stress"),
        func.avg(Entry.sleep_hours).label("avg_sleep"),
    ).where(
        Entry.user_id == user_id,
        Entry.entry_date >= date_from,
        Entry.entry_date <= date_to,
    )
    agg_result = (await db.execute(agg_stmt)).one()

    # Mood trend (daily points)
    trend_stmt = (
        select(Entry)
        .where(
            Entry.user_id == user_id,
            Entry.entry_date >= date_from,
            Entry.entry_date <= date_to,
        )
        .order_by(Entry.entry_date.asc())
    )
    trend_result = await db.execute(trend_stmt)
    entries = list(trend_result.scalars().all())

    # Get AI analyses for sentiment data
    entry_ids = [e.id for e in entries]
    sentiment_map: dict[UUID, float] = {}
    if entry_ids:
        ai_stmt = select(AIAnalysis).where(AIAnalysis.entry_id.in_(entry_ids))
        ai_result = await db.execute(ai_stmt)
        analyses = list(ai_result.scalars().all())
        sentiment_map = {a.entry_id: a.sentiment_score for a in analyses}

    mood_trend = [
        MoodTrendPoint(
            date=e.entry_date,
            mood_score=e.mood_score,
            stress_score=e.stress_score,
            sleep_hours=e.sleep_hours,
            sentiment_score=sentiment_map.get(e.id),
        )
        for e in entries
    ]

    # Top tags from AI analyses
    tag_counter: Counter[str] = Counter()
    sentiment_values: list[float] = []

    if entry_ids:
        ai_stmt = select(AIAnalysis).where(
            AIAnalysis.entry_id.in_(entry_ids),
        )
        ai_result = await db.execute(ai_stmt)
        for analysis in ai_result.scalars().all():
            if analysis.extracted_tags:
                for tag in analysis.extracted_tags:
                    tag_counter[tag] += 1
            sentiment_values.append(analysis.sentiment_score)

    top_tags = [
        TagCount(tag=tag, count=count)
        for tag, count in tag_counter.most_common(10)
    ]

    sentiment_avg = (
        sum(sentiment_values) / len(sentiment_values)
        if sentiment_values
        else None
    )

    return AnalyticsSummary(
        period_from=date_from,
        period_to=date_to,
        total_entries=agg_result.total or 0,
        avg_mood=round(float(agg_result.avg_mood or 0), 1),
        avg_stress=round(float(agg_result.avg_stress or 0), 1),
        avg_sleep=round(float(agg_result.avg_sleep or 0), 1),
        mood_trend=mood_trend,
        top_tags=top_tags,
        sentiment_avg=round(sentiment_avg, 2) if sentiment_avg else None,
    )


async def get_correlation_insights(
    db: AsyncSession,
    user_id: UUID,
    date_from: date,
    date_to: date,
) -> CorrelationInsights:
    """Compute tag-metric correlations for insight generation."""
    # Fetch all entries with their AI analyses
    stmt = (
        select(Entry)
        .where(
            Entry.user_id == user_id,
            Entry.entry_date >= date_from,
            Entry.entry_date <= date_to,
        )
    )
    result = await db.execute(stmt)
    entries = list(result.scalars().all())

    entry_ids = [e.id for e in entries]
    entry_map = {e.id: e for e in entries}

    # Fetch AI analyses
    tag_entries: dict[str, list[Entry]] = {}
    all_tags: set[str] = set()

    if entry_ids:
        ai_stmt = select(AIAnalysis).where(AIAnalysis.entry_id.in_(entry_ids))
        ai_result = await db.execute(ai_stmt)
        for analysis in ai_result.scalars().all():
            entry = entry_map.get(analysis.entry_id)
            if not entry or not analysis.extracted_tags:
                continue
            for tag in analysis.extracted_tags:
                all_tags.add(tag)
                tag_entries.setdefault(tag, []).append(entry)

    insights: list[InsightItem] = []

    # Compute correlations for tags that appear >= 3 times
    for tag in all_tags:
        tagged = tag_entries.get(tag, [])
        if len(tagged) < 3:
            continue

        tagged_ids = {e.id for e in tagged}
        non_tagged = [e for e in entries if e.id not in tagged_ids]
        if not non_tagged:
            continue

        avg_sleep_with = sum(e.sleep_hours for e in tagged) / len(tagged)
        avg_sleep_without = sum(e.sleep_hours for e in non_tagged) / len(non_tagged)
        avg_stress_with = sum(e.stress_score for e in tagged) / len(tagged)
        avg_stress_without = sum(e.stress_score for e in non_tagged) / len(non_tagged)
        avg_mood_with = sum(e.mood_score for e in tagged) / len(tagged)
        avg_mood_without = sum(e.mood_score for e in non_tagged) / len(non_tagged)

        # Only flag significant differences
        sleep_diff = abs(avg_sleep_with - avg_sleep_without)
        stress_diff = abs(avg_stress_with - avg_stress_without)
        mood_diff = abs(avg_mood_with - avg_mood_without)

        if sleep_diff < 0.5 and stress_diff < 1.0 and mood_diff < 1.0:
            continue

        # Build description
        parts: list[str] = []
        if sleep_diff >= 0.5:
            direction = "падает" if avg_sleep_with < avg_sleep_without else "растёт"
            parts.append(
                f"сон {direction} на ~{sleep_diff:.1f}ч"
            )
        if stress_diff >= 1.0:
            direction = "растёт" if avg_stress_with > avg_stress_without else "падает"
            parts.append(
                f"стресс {direction} до {avg_stress_with:.0f}/10"
            )
        if mood_diff >= 1.0:
            direction = "падает" if avg_mood_with < avg_mood_without else "растёт"
            parts.append(
                f"настроение {direction} до {avg_mood_with:.0f}/10"
            )

        description = (
            f"В дни, когда ты упоминаешь «{tag}», " + ", ".join(parts) + "."
        )

        insights.append(
            InsightItem(
                type="tag_correlation",
                tag=tag,
                description=description,
                metrics=CorrelationMetrics(
                    avg_sleep_with_tag=round(avg_sleep_with, 1),
                    avg_sleep_without_tag=round(avg_sleep_without, 1),
                    avg_stress_with_tag=round(avg_stress_with, 1),
                    avg_stress_without_tag=round(avg_stress_without, 1),
                    avg_mood_with_tag=round(avg_mood_with, 1),
                    avg_mood_without_tag=round(avg_mood_without, 1),
                ),
            )
        )

    # Trend insight (last 7 entries)
    recent = sorted(entries, key=lambda e: e.entry_date)[-7:]
    if len(recent) >= 3:
        first_mood = recent[0].mood_score
        last_mood = recent[-1].mood_score
        if last_mood - first_mood >= 2:
            insights.append(
                InsightItem(
                    type="trend",
                    description=(
                        f"Последние {len(recent)} дней твоё настроение стабильно "
                        f"растёт: с {first_mood} до {last_mood}. Так держать! 🚀"
                    ),
                )
            )
        elif first_mood - last_mood >= 2:
            insights.append(
                InsightItem(
                    type="trend",
                    description=(
                        f"Последние {len(recent)} дней настроение снижается: "
                        f"с {first_mood} до {last_mood}. Позаботься о себе 💜"
                    ),
                )
            )

    return CorrelationInsights(
        insights=insights,
        generated_at=datetime.now(timezone.utc),
    )
