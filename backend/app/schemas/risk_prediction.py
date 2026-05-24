from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RiskPredictionRequest(BaseModel):
    """Farmer request for agriculture risk prediction."""

    crop: str = Field(..., description="Crop name (e.g., paddy, tomato, cotton)")
    location: Optional[str] = Field(None, description="Location/region/state")
    weather_conditions: Optional[str] = Field(None, description="Current/recent weather details")
    soil_condition: Optional[str] = Field(None, description="Soil condition details")
    disease_signals: Optional[str] = Field(None, description="Observed disease indicators")
    market_signals: Optional[str] = Field(None, description="Observed market indicators")
    pest_signals: Optional[str] = Field(None, description="Observed pest indicators")
    irrigation_status: Optional[str] = Field(None, description="Irrigation availability/stress")
    context: Optional[str] = Field(None, description="Any additional farmer context")

    @field_validator("crop", mode="before")
    @classmethod
    def validate_crop(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("crop must be a string")
        value = value.strip()
        if len(value) < 2:
            raise ValueError("crop must be at least 2 characters")
        return value


class PreventiveActions(BaseModel):
    """Time-horizon grouped preventive actions."""

    immediate: str
    short_term: str
    long_term: str


class RiskPredictionResult(BaseModel):
    """Structured agriculture risk prediction result from AI."""

    crop: str
    location: str
    overall_risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    risk_score: float = Field(..., ge=0.0, le=1.0)
    key_risks: list[str] = Field(default_factory=list)
    weather_risk_analysis: str
    disease_risk_analysis: str
    market_risk_analysis: str
    short_term_forecast: str
    long_term_forecast: str
    preventive_actions: PreventiveActions
    farmer_alert_message: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class RiskPredictionResponse(BaseModel):
    """API response wrapper for agriculture risk prediction."""

    success: bool
    crop: str
    location: Optional[str]
    analysis: RiskPredictionResult
