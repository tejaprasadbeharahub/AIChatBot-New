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
    AGRICULTURE_SYSTEM_PROMPT,
    AGRICULTURE_USER_PROMPT,
)
from app.core.config import settings
from app.models.crop_diagnosis import CropDiagnosis
from app.schemas.agriculture import AgricultureDiagnosisResult

logger = logging.getLogger(__name__)


class AgricultureServiceError(Exception):
    """Raised when diagnosis generation fails."""


class AgricultureService:
    """AI-powered crop disease diagnosis service with Supabase persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _resolve_model(self) -> str:
        return settings.n8n_classification_model or settings.llm_model or "gpt-4o"

    def _extract_json(self, text: str) -> dict[str, Any]:
        content = text.strip()
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if fenced:
            content = fenced.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            inline = re.search(r"\{.*\}", content, re.DOTALL)
            if inline:
                return json.loads(inline.group(0))
            raise

    def _persist(self, query: str, crop_type: Optional[str], region: Optional[str],
                  weather: Optional[str], soil_type: Optional[str],
                  symptoms: Optional[str], result: AgricultureDiagnosisResult) -> None:
        """Save diagnosis to Supabase crop_diagnoses table."""
        try:
            record = CropDiagnosis(
                query=query,
                crop_type=crop_type,
                region=region,
                weather=weather,
                soil_type=soil_type,
                symptoms=symptoms,
                disease_name=result.disease_name,
                scientific_name=result.scientific_name,
                confidence_score=result.confidence_score,
                urgency_level=result.urgency_level,
                affected_parts=result.affected_parts,
                symptoms_matched=result.symptoms_matched,
                likely_causes=result.likely_causes,
                treatment_steps=result.treatment_steps,
                organic_solutions=result.organic_solutions,
                chemical_solutions=result.chemical_solutions,
                preventive_measures=result.preventive_measures,
                best_season_to_act=result.best_season_to_act,
                additional_notes=result.additional_notes,
            )
            self._db.add(record)
            self._db.commit()
            logger.info(
                "agriculture_diagnosis_persisted",
                extra={"event": "agriculture_diagnosis_persisted", "disease": result.disease_name},
            )
        except SQLAlchemyError:
            self._db.rollback()
            logger.exception("agriculture_diagnosis_persist_failed")
            # Do not raise — persistence failure must not block the API response

    async def diagnose(
        self,
        query: str,
        crop_type: Optional[str],
        region: Optional[str],
        weather: Optional[str],
        soil_type: Optional[str],
        symptoms: Optional[str],
    ) -> AgricultureDiagnosisResult:
        retries = max(settings.n8n_classification_retry_attempts, 1)
        timeout_seconds = max(settings.n8n_classification_timeout_seconds, 30)
        model_name = self._resolve_model()

        user_prompt = AGRICULTURE_USER_PROMPT.format(
            query=query,
            crop_type=crop_type or "Not specified",
            region=region or "Not specified (assume typical Indian farming region)",
            weather=weather or "Not specified",
            soil_type=soil_type or "Not specified",
            symptoms=symptoms or "See query above",
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
                            {"role": "system", "content": AGRICULTURE_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    ),
                    timeout=timeout_seconds,
                )

                content = response.choices[0].message.content if response.choices else ""
                parsed = self._extract_json(str(content or ""))
                result = AgricultureDiagnosisResult.model_validate(parsed)

                logger.info(
                    "agriculture_diagnosis_success",
                    extra={
                        "event": "agriculture_diagnosis_success",
                        "disease": result.disease_name,
                        "confidence": result.confidence_score,
                        "attempt": attempt,
                    },
                )
                self._persist(query, crop_type, region, weather, soil_type, symptoms, result)
                return result

            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "agriculture_diagnosis_retry",
                    extra={"event": "agriculture_diagnosis_retry", "attempt": attempt, "error": str(exc)},
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "agriculture_diagnosis_provider_error",
                    extra={"event": "agriculture_diagnosis_provider_error", "attempt": attempt, "error": str(exc)},
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

        # Fallback when all retries fail
        if settings.n8n_classification_enable_fallback:
            logger.warning("agriculture_diagnosis_fallback", extra={"error": str(last_error)})
            fallback = AgricultureDiagnosisResult(
                disease_name="Unable to determine — insufficient data or service unavailable",
                confidence_score=0.0,
                urgency_level="medium",
                symptoms_matched=[],
                likely_causes=["Diagnosis service temporarily unavailable"],
                treatment_steps=["Please consult a local agricultural extension officer (KVK)"],
                organic_solutions=[],
                chemical_solutions=[],
                preventive_measures=[],
                additional_notes=f"Diagnosis could not be completed. Error: {last_error}",
            )
            self._persist(query, crop_type, region, weather, soil_type, symptoms, fallback)
            return fallback

        raise AgricultureServiceError(f"Diagnosis failed after {retries} attempts: {last_error}")
