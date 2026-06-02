from __future__ import annotations

from datetime import datetime, timezone
import json
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_workflow_db
from app.models.crop_diagnosis import CropDiagnosis
from app.models.market_intelligence import MarketIntelligence
from app.models.risk_prediction import RiskPrediction
from app.schemas.agriculture import (
    AgricultureDiagnosisRequest,
    AgricultureDiagnosisResponse,
    FarmCurrentQueryResponse,
    FarmQuerySubmissionRequest,
    FarmQuerySubmissionResponse,
)
from app.schemas.market_intelligence import (
    MarketIntelligenceRequest,
    MarketIntelligenceResponse,
)
from app.schemas.risk_prediction import (
    RiskPredictionRequest,
    RiskPredictionResponse,
)
from app.services.agriculture_service import AgricultureService, AgricultureServiceError
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
    MarketIntelligenceServiceError,
)
from app.services.risk_prediction_service import (
    RiskPredictionService,
    RiskPredictionServiceError,
)

router = APIRouter(prefix="/farm", tags=["farm"])
logger = logging.getLogger(__name__)
STATIC_FARMER_ID = "F001"


def _pick_first_non_empty(*values: object) -> str | None:
    """Return the first non-empty string-like value from a list of candidates."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _extract_location_from_context(context: object) -> str | None:
    """Extract a location-like field from context payloads or JSON-encoded strings."""
    if context is None:
        return None

    data: object = context
    if isinstance(context, str):
        text = context.strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except (TypeError, ValueError):
            return None

    if not isinstance(data, dict):
        return None

    # Common payload shapes that may contain location/region information.
    nested_candidates = [
        data,
        data.get("initial_input") if isinstance(data.get("initial_input"), dict) else None,
        data.get("input") if isinstance(data.get("input"), dict) else None,
        data.get("payload") if isinstance(data.get("payload"), dict) else None,
    ]

    for candidate in nested_candidates:
        if not isinstance(candidate, dict):
            continue
        location = _pick_first_non_empty(
            candidate.get("location"),
            candidate.get("region"),
            candidate.get("district"),
            candidate.get("state"),
            candidate.get("city"),
        )
        if location:
            return location

    return None


@router.get("/current-query", response_model=FarmCurrentQueryResponse)
async def get_current_farm_query(
    db: Session = Depends(get_workflow_db),
) -> FarmCurrentQueryResponse:
    """Return latest persisted farm query initial input details for AI agriculture assistant."""
    latest_risk = db.query(RiskPrediction).order_by(RiskPrediction.created_at.desc()).first()
    latest_diagnosis = db.query(CropDiagnosis).order_by(CropDiagnosis.created_at.desc()).first()
    latest_market = db.query(MarketIntelligence).order_by(MarketIntelligence.created_at.desc()).first()

    candidates: list[tuple[str, str, datetime, dict]] = []

    if latest_risk:
        candidates.append(
            (
                "risk_prediction",
                str(latest_risk.id),
                latest_risk.created_at,
                {
                    "crop": latest_risk.crop,
                    "location": _pick_first_non_empty(
                        latest_risk.location,
                        _extract_location_from_context(latest_risk.context),
                    ),
                    "weather_conditions": latest_risk.weather_conditions,
                    "soil_condition": latest_risk.soil_condition,
                    "disease_signals": latest_risk.disease_signals,
                    "market_signals": latest_risk.market_signals,
                    "pest_signals": latest_risk.pest_signals,
                    "irrigation_status": latest_risk.irrigation_status,
                    "context": latest_risk.context,
                    "overall_risk_level": latest_risk.overall_risk_level,
                    "risk_score": latest_risk.risk_score,
                    "confidence": latest_risk.confidence,
                    "farmer_alert_message": latest_risk.farmer_alert_message,
                },
            )
        )

    if latest_diagnosis:
        candidates.append(
            (
                "crop_diagnosis",
                str(latest_diagnosis.id),
                latest_diagnosis.created_at,
                {
                    "query": latest_diagnosis.query,
                    "crop_type": latest_diagnosis.crop_type,
                    "location": latest_diagnosis.region,
                    "region": latest_diagnosis.region,
                    "weather": latest_diagnosis.weather,
                    "soil_type": latest_diagnosis.soil_type,
                    "symptoms": latest_diagnosis.symptoms,
                    "disease_name": latest_diagnosis.disease_name,
                    "confidence_score": latest_diagnosis.confidence_score,
                    "urgency_level": latest_diagnosis.urgency_level,
                },
            )
        )

    if latest_market:
        candidates.append(
            (
                "market_intelligence",
                str(latest_market.id),
                latest_market.created_at,
                {
                    "crop": latest_market.crop,
                    "location": _pick_first_non_empty(
                        latest_market.region,
                        _extract_location_from_context(latest_market.context),
                    ),
                    "region": latest_market.region,
                    "current_price": latest_market.current_price,
                    "quantity": latest_market.quantity,
                    "storage_available": latest_market.storage_available,
                    "weather": latest_market.weather,
                    "context": latest_market.context,
                    "recommended_action": latest_market.recommended_action,
                    "risk_level": latest_market.risk_level,
                    "confidence": latest_market.confidence,
                    "current_market_trend": latest_market.current_market_trend,
                },
            )
        )

    if not candidates:
        raise HTTPException(status_code=404, detail="No farm query details found")

    source, record_id, created_at, initial_input = max(
        candidates,
        key=lambda item: item[2] or datetime.min.replace(tzinfo=timezone.utc),
    )

    # Normalize location across different sources to keep frontend rendering consistent.
    initial_input["location"] = _pick_first_non_empty(
        initial_input.get("location"),
        initial_input.get("region"),
    )

    return FarmCurrentQueryResponse(
        success=True,
        source=source,
        record_id=record_id,
        created_at=created_at,
        initial_input=initial_input,
    )


async def _post_to_n8n_webhook(payload: dict) -> dict | None:
    webhook_url = (settings.n8n_workflow_webhook_url or "").strip()
    if not webhook_url:
        raise AgricultureServiceError("N8N_WEBHOOK_URL is not configured")

    timeout_seconds = max(settings.n8n_workflow_timeout_seconds, 5)
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type.lower():
                return response.json()
            return {"raw_response": response.text}
    except httpx.HTTPError as exc:
        logger.warning("farm_query_n8n_webhook_failed", extra={"error": str(exc)})
        raise AgricultureServiceError("Failed to create farm query via N8N webhook") from exc


@router.post("/submit-query", response_model=FarmQuerySubmissionResponse)
async def submit_farm_query(payload: FarmQuerySubmissionRequest) -> FarmQuerySubmissionResponse:
    """Public endpoint used by frontend to submit farm query to N8N webhook."""
    webhook_payload = {
        "event": "farm-ticket",
        "farmer_id": STATIC_FARMER_ID,
        "query": payload.query,
        "crop_type": payload.crop_type,
        "location": payload.location,
        "region": payload.location,
        "weather": payload.weather,
    }

    try:
        result = await _post_to_n8n_webhook(webhook_payload)
    except AgricultureServiceError as exc:
        logger.warning("farm_submit_query_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("farm_submit_query_unhandled_error")
        raise HTTPException(status_code=500, detail="Farm query submission failed") from exc

    return FarmQuerySubmissionResponse(
        success=True,
        message="Farm query forwarded to N8N successfully",
        submitted_payload=webhook_payload,
        result=result,
    )


@router.post("/diagnose", response_model=AgricultureDiagnosisResponse)
async def diagnose_crop(
    payload: AgricultureDiagnosisRequest,
    db: Session = Depends(get_workflow_db),
) -> AgricultureDiagnosisResponse:
    """
    Agricultural AI Doctor — diagnose crop diseases from farmer-described symptoms.

    Powered by LiteLLM (Gemini/GPT-4o). Returns structured JSON with:
    - Disease identification + confidence score
    - Urgency level
    - Organic and chemical treatment options
    - Preventive measures for Indian farming conditions
    All diagnosis records are persisted to Supabase (SUPABASE_DATABASE_URL).
    """
    service = AgricultureService(db)
    effective_region = _pick_first_non_empty(payload.region, payload.location)

    try:
        diagnosis = await service.diagnose(
            query=payload.query,
            crop_type=payload.crop_type,
            region=effective_region,
            weather=payload.weather,
            soil_type=payload.soil_type,
            symptoms=payload.symptoms,
        )
    except AgricultureServiceError as exc:
        logger.warning("agriculture_diagnose_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("agriculture_diagnose_unhandled_error")
        raise HTTPException(status_code=500, detail="Crop diagnosis failed") from exc

    return AgricultureDiagnosisResponse(
        success=True,
        crop_type=payload.crop_type,
        region=effective_region,
        diagnosis=diagnosis,
    )


@router.post("/market-advice", response_model=MarketIntelligenceResponse)
async def market_intelligence(
    payload: MarketIntelligenceRequest,
    db: Session = Depends(get_workflow_db),
) -> MarketIntelligenceResponse:
    """
    Agricultural Market Intelligence — advise farmers on optimal crop selling timing.

    Powered by LiteLLM (Gemini/GPT-4o). Returns structured JSON with:
    - Current market trend (UP / DOWN / STABLE)
    - Recommended action (SELL_NOW / HOLD / WAIT)
    - Best selling window in days
    - Expected profit change %
    - Risk level and farmer-friendly advice
    All analysis records are persisted to Supabase (SUPABASE_DATABASE_URL).
    """
    service = MarketIntelligenceService(db)
    effective_region = _pick_first_non_empty(payload.region, payload.location)

    try:
        analysis = await service.analyze(
            crop=payload.crop,
            region=effective_region,
            current_price=payload.current_price,
            quantity=payload.quantity,
            storage_available=payload.storage_available,
            weather=payload.weather,
            context=payload.context,
        )
    except MarketIntelligenceServiceError as exc:
        logger.warning("market_intelligence_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("market_intelligence_unhandled_error")
        raise HTTPException(status_code=500, detail="Market analysis failed") from exc

    return MarketIntelligenceResponse(
        success=True,
        crop=payload.crop,
        region=effective_region,
        analysis=analysis,
    )


@router.post("/recommend", response_model=RiskPredictionResponse)
async def risk_prediction(
    payload: RiskPredictionRequest,
    db: Session = Depends(get_workflow_db),
) -> RiskPredictionResponse:
    """
    Agricultural Risk Prediction - detect near-term and long-term farming risks.

    Powered by LiteLLM (Gemini/GPT-4o). Returns structured JSON with:
    - Overall risk level and normalized risk score
    - Key weather, disease, and market risks
    - Preventive actions by immediate/short-term/long-term windows
    All analysis records are persisted to Supabase (SUPABASE_DATABASE_URL).
    """
    service = RiskPredictionService(db)

    try:
        analysis = await service.predict(
            crop=payload.crop,
            location=payload.location,
            weather_conditions=payload.weather_conditions,
            soil_condition=payload.soil_condition,
            disease_signals=payload.disease_signals,
            market_signals=payload.market_signals,
            pest_signals=payload.pest_signals,
            irrigation_status=payload.irrigation_status,
            context=payload.context,
        )
    except RiskPredictionServiceError as exc:
        logger.warning("risk_prediction_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("risk_prediction_unhandled_error")
        raise HTTPException(status_code=500, detail="Risk prediction failed") from exc

    return RiskPredictionResponse(
        success=True,
        crop=payload.crop,
        location=payload.location,
        analysis=analysis,
    )

