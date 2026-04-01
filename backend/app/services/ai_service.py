import json
import logging
import time
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.database import async_session_maker
from app.crud.entry import save_ai_analysis
from app.models.entry import AIStatus, Entry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant that analyzes mood diary entries.
Given a diary entry text along with the user's mood (1-10), stress (1-10), and sleep hours,
analyze the text and return a JSON object with exactly these fields:

1. "sentiment_score": a float from -1.0 (very negative) to 1.0 (very positive) based on the text tone.
2. "extracted_tags": an array of 2-6 key themes/topics found in the text, in the same language as the input. Examples: ["работа", "спорт", "семья", "дедлайн"].
3. "insight": a brief, empathetic 1-2 sentence observation about the entry, in the same language as the input.

Return ONLY valid JSON, no markdown, no extra text."""


async def analyze_entry_background(
    entry_id: UUID,
    note_text: str,
    mood_score: int,
    stress_score: int,
    sleep_hours: float,
) -> None:
    """Background task: call AI API and save analysis results."""
    start_time = time.monotonic()

    async with async_session_maker() as db:
        try:
            # Mark as processing
            entry = await db.get(Entry, entry_id)
            if not entry:
                logger.error(f"Entry {entry_id} not found for AI analysis")
                return
            entry.ai_status = AIStatus.PROCESSING
            await db.commit()

            # Call AI
            result = await _call_ai_api(
                note_text, mood_score, stress_score, sleep_hours,
            )

            processing_time_ms = int((time.monotonic() - start_time) * 1000)

            # Save results
            await save_ai_analysis(
                db=db,
                entry_id=entry_id,
                sentiment_score=result["sentiment_score"],
                extracted_tags=result["extracted_tags"],
                insight=result.get("insight"),
                model_name=settings.AI_MODEL,
                processing_time_ms=processing_time_ms,
            )
            await db.commit()

            logger.info(
                f"AI analysis complete for entry {entry_id} "
                f"in {processing_time_ms}ms"
            )

        except Exception as e:
            logger.exception(f"AI analysis failed for entry {entry_id}: {e}")
            # Mark as failed
            entry = await db.get(Entry, entry_id)
            if entry:
                entry.ai_status = AIStatus.FAILED
                await db.commit()


async def _call_ai_api(
    note_text: str,
    mood_score: int,
    stress_score: int,
    sleep_hours: float,
) -> dict:
    """Call OpenAI-compatible API and parse structured response."""
    user_message = (
        f"Diary entry:\n"
        f"Mood: {mood_score}/10, Stress: {stress_score}/10, Sleep: {sleep_hours}h\n"
        f"Text: {note_text}"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.AI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.AI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            },
        )
        response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()

    # Parse JSON from response (handle potential markdown wrapping)
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    result = json.loads(content)

    # Validate and sanitize
    return {
        "sentiment_score": max(-1.0, min(1.0, float(result["sentiment_score"]))),
        "extracted_tags": [str(t) for t in result.get("extracted_tags", [])],
        "insight": result.get("insight"),
    }
