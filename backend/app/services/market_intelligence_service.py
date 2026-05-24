from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Optional

from litellm import acompletion
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.agriculture_prompt import (
    AGRI_MARKET_INTELLIGENCE_PROMPT,
    AGRI_MARKET_INTELLIGENCE_USER_PROMPT,
)
from app.core.config import settings
from app.models.market_intelligence import MarketIntelligence
from app.schemas.market_intelligence import MarketIntelligenceResult

logger = logging.getLogger(__name__)


class MarketIntelligenceServiceError(Exception):
    """Raised when market analysis generation fails."""


class MarketIntelligenceService:
    """AI-powered crop market intelligence with Supabase persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_model(self) -> str:
        model = settings.llm_model or "gemini-2.0-flash"
        proxy = settings.litellm_proxy_url or ""
        if proxy and not model.startswith("openai/") and "/" not in model:
            return f"openai/{model}"
        return model

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Strip markdown fences and parse first JSON object found."""
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
        text = re.sub(r"```$", "", text.strip())
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON object found in response: {text[:200]!r}")
        return json.loads(text[start:end])

    def _persist(
        self,
        crop: str,
        region: Optional[str],
        current_price: Optional[str],
        quantity: Optional[str],
        storage_available: Optional[str],
        weather: Optional[str],
        context: Optional[str],
        result: MarketIntelligenceResult,
    ) -> None:
        """Persist market intelligence result to Supabase."""
        try:
            record = MarketIntelligence(
                crop=crop,
                region=region,
                current_price=current_price,
                quantity=quantity,
                storage_available=storage_available,
                weather=weather,
                context=context,
                current_market_trend=result.current_market_trend,
                price_outlook=result.price_outlook,
                recommended_action=result.recommended_action,
                best_selling_window_days=result.best_selling_window_days,
                expected_profit_change_percent=result.expected_profit_change_percent,
                risk_level=result.risk_level,
                reasoning=result.reasoning,
                farmer_advice=result.farmer_advice,
                confidence=result.confidence,
            )
            self._db.add(record)
            self._db.commit()
            logger.info(
                "market_intelligence_persisted",
                extra={
                    "event": "market_intelligence_persisted",
                    "crop": crop,
                    "action": result.recommended_action,
                },
            )
        except SQLAlchemyError:
            self._db.rollback()
            logger.exception("market_intelligence_persist_failed")
            # Do not raise — persistence failure must not block the API response

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        crop: str,
        region: Optional[str],
        current_price: Optional[str],
        quantity: Optional[str],
        storage_available: Optional[str],
        weather: Optional[str],
        context: Optional[str],
    ) -> MarketIntelligenceResult:
        retries = max(settings.n8n_classification_retry_attempts, 1)
        timeout_seconds = max(settings.n8n_classification_timeout_seconds, 30)
        model_name = self._resolve_model()

        user_prompt = AGRI_MARKET_INTELLIGENCE_USER_PROMPT.format(
            crop=crop,
            region=region or "Not specified (assume typical Indian farming region)",
            current_price=current_price or "Not specified",
            quantity=quantity or "Not specified",
            storage_available=storage_available or "Not specified",
            weather=weather or "Not specified",
            context=context or "None",
        )

        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                response = await asyncio.wait_for(
                    acompletion(
                        model=model_name,
                        base_url=settings.litellm_proxy_url,
                        api_key=settings.litellm_api_key,
                        temperature=0.3,
                        messages=[
                            {"role": "system", "content": AGRI_MARKET_INTELLIGENCE_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    ),
                    timeout=timeout_seconds,
                )

                content = response.choices[0].message.content if response.choices else ""
                parsed = self._extract_json(str(content or ""))
                result = MarketIntelligenceResult.model_validate(parsed)

                logger.info(
                    "market_intelligence_success",
                    extra={
                        "event": "market_intelligence_success",
                        "crop": crop,
                        "action": result.recommended_action,
                        "trend": result.current_market_trend,
                        "attempt": attempt,
                    },
                )
                self._persist(crop, region, current_price, quantity, storage_available, weather, context, result)
                return result

            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "market_intelligence_retry",
                    extra={"event": "market_intelligence_retry", "attempt": attempt, "error": str(exc)},
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "market_intelligence_provider_error",
                    extra={"event": "market_intelligence_provider_error", "attempt": attempt, "error": str(exc)},
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

        # Fallback
        if settings.n8n_classification_enable_fallback:
            logger.warning("market_intelligence_fallback", extra={"error": str(last_error)})
            fallback = MarketIntelligenceResult(
                crop=crop,
                current_market_trend="STABLE",
                price_outlook="Unable to determine — market analysis service temporarily unavailable.",
                recommended_action="HOLD",
                best_selling_window_days=0,
                expected_profit_change_percent=0.0,
                risk_level="MEDIUM",
                reasoning="Market analysis could not be completed due to a service error.",
                farmer_advice="Please consult your local mandi or agricultural officer for current price trends.",
                confidence=0.0,
            )
            self._persist(crop, region, current_price, quantity, storage_available, weather, context, fallback)
            return fallback

        raise MarketIntelligenceServiceError(f"Market analysis failed after {retries} attempts: {last_error}")
