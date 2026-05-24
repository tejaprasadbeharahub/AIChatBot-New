from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_workflow_db
from app.schemas.agriculture import (
    AgricultureDiagnosisRequest,
    AgricultureDiagnosisResponse,
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

    try:
        diagnosis = await service.diagnose(
            query=payload.query,
            crop_type=payload.crop_type,
            region=payload.region,
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
        region=payload.region,
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

    try:
        analysis = await service.analyze(
            crop=payload.crop,
            region=payload.region,
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
        region=payload.region,
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

