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
    AGRI_RISK_PREDICTION_PROMPT,
    AGRI_RISK_PREDICTION_USER_PROMPT,
)
from app.core.config import settings
from app.models.risk_prediction import RiskPrediction
from app.schemas.risk_prediction import PreventiveActions, RiskPredictionResult

logger = logging.getLogger(__name__)


class RiskPredictionServiceError(Exception):
    """Raised when risk prediction generation fails."""


class RiskPredictionService:
    """AI-powered agriculture risk prediction with Supabase persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _resolve_model(self) -> str:
        model = settings.llm_model or "gemini-2.0-flash"
        proxy = settings.litellm_proxy_url or ""
        if proxy and not model.startswith("openai/") and "/" not in model:
            return f"openai/{model}"
        return model

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
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
        location: Optional[str],
        weather_conditions: Optional[str],
        soil_condition: Optional[str],
        disease_signals: Optional[str],
        market_signals: Optional[str],
        pest_signals: Optional[str],
        irrigation_status: Optional[str],
        context: Optional[str],
        result: RiskPredictionResult,
    ) -> None:
        try:
            record = RiskPrediction(
                crop=crop,
                location=location,
                weather_conditions=weather_conditions,
                soil_condition=soil_condition,
                disease_signals=disease_signals,
                market_signals=market_signals,
                pest_signals=pest_signals,
                irrigation_status=irrigation_status,
                context=context,
                overall_risk_level=result.overall_risk_level,
                risk_score=result.risk_score,
                key_risks=result.key_risks,
                weather_risk_analysis=result.weather_risk_analysis,
                disease_risk_analysis=result.disease_risk_analysis,
                market_risk_analysis=result.market_risk_analysis,
                short_term_forecast=result.short_term_forecast,
                long_term_forecast=result.long_term_forecast,
                preventive_actions=result.preventive_actions.model_dump(),
                farmer_alert_message=result.farmer_alert_message,
                confidence=result.confidence,
            )
            self._db.add(record)
            self._db.commit()
            logger.info(
                "risk_prediction_persisted",
                extra={
                    "event": "risk_prediction_persisted",
                    "crop": crop,
                    "risk_level": result.overall_risk_level,
                },
            )
        except SQLAlchemyError:
            self._db.rollback()
            logger.exception("risk_prediction_persist_failed")

    async def predict(
        self,
        crop: str,
        location: Optional[str],
        weather_conditions: Optional[str],
        soil_condition: Optional[str],
        disease_signals: Optional[str],
        market_signals: Optional[str],
        pest_signals: Optional[str],
        irrigation_status: Optional[str],
        context: Optional[str],
    ) -> RiskPredictionResult:
        retries = max(settings.n8n_classification_retry_attempts, 1)
        timeout_seconds = max(settings.n8n_classification_timeout_seconds, 30)
        model_name = self._resolve_model()

        user_prompt = AGRI_RISK_PREDICTION_USER_PROMPT.format(
            crop=crop,
            location=location or "Not specified (assume typical Indian farming location)",
            weather_conditions=weather_conditions or "Not specified",
            soil_condition=soil_condition or "Not specified",
            disease_signals=disease_signals or "Not specified",
            market_signals=market_signals or "Not specified",
            pest_signals=pest_signals or "Not specified",
            irrigation_status=irrigation_status or "Not specified",
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
                            {"role": "system", "content": AGRI_RISK_PREDICTION_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    ),
                    timeout=timeout_seconds,
                )

                content = response.choices[0].message.content if response.choices else ""
                parsed = self._extract_json(str(content or ""))
                result = RiskPredictionResult.model_validate(parsed)

                logger.info(
                    "risk_prediction_success",
                    extra={
                        "event": "risk_prediction_success",
                        "crop": crop,
                        "risk_level": result.overall_risk_level,
                        "attempt": attempt,
                    },
                )
                self._persist(
                    crop,
                    location,
                    weather_conditions,
                    soil_condition,
                    disease_signals,
                    market_signals,
                    pest_signals,
                    irrigation_status,
                    context,
                    result,
                )
                return result

            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "risk_prediction_retry",
                    extra={"event": "risk_prediction_retry", "attempt": attempt, "error": str(exc)},
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "risk_prediction_provider_error",
                    extra={"event": "risk_prediction_provider_error", "attempt": attempt, "error": str(exc)},
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

        if settings.n8n_classification_enable_fallback:
            logger.warning("risk_prediction_fallback", extra={"error": str(last_error)})
            fallback = RiskPredictionResult(
                crop=crop,
                location=location or "Unknown",
                overall_risk_level="MEDIUM",
                risk_score=0.5,
                key_risks=["insufficient data risk"],
                weather_risk_analysis="Unable to compute weather-linked risk due to temporary service issue.",
                disease_risk_analysis="Disease risk could not be estimated reliably.",
                market_risk_analysis="Market risk could not be estimated reliably.",
                short_term_forecast="Short-term risk outlook is uncertain due to unavailable model response.",
                long_term_forecast="Long-term risk outlook is uncertain due to unavailable model response.",
                preventive_actions=PreventiveActions(
                    immediate="Inspect crop daily and maintain basic moisture and hygiene control.",
                    short_term="Consult local agricultural officer for location-specific guidance.",
                    long_term="Adopt resilient crop planning, pest monitoring, and irrigation planning.",
                ),
                farmer_alert_message="Risk prediction service is temporarily unavailable; use local advisory support.",
                confidence=0.0,
            )
            self._persist(
                crop,
                location,
                weather_conditions,
                soil_condition,
                disease_signals,
                market_signals,
                pest_signals,
                irrigation_status,
                context,
                fallback,
            )
            return fallback

        raise RiskPredictionServiceError(f"Risk prediction failed after {retries} attempts: {last_error}")
