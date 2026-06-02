from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class MarketIntelligenceRequest(BaseModel):
    """Farmer request for crop market analysis."""

    crop: str = Field(..., description="Crop name (e.g., wheat, tomato, onion)")
    region: Optional[str] = Field(None, description="Region or state in India")
    location: Optional[str] = Field(None, description="Location alias used by external workflows")
    current_price: Optional[str] = Field(None, description="Current market price per quintal/kg")
    quantity: Optional[str] = Field(None, description="Quantity available to sell (kg or quintal)")
    storage_available: Optional[str] = Field(None, description="Storage availability (Yes/No or duration)")
    weather: Optional[str] = Field(None, description="Recent or current weather conditions")
    context: Optional[str] = Field(None, description="Any additional context from the farmer")

    @field_validator("crop", mode="before")
    @classmethod
    def validate_crop(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("crop must be a string")
        value = value.strip()
        if len(value) < 2:
            raise ValueError("crop must be at least 2 characters")
        return value


class MarketIntelligenceResult(BaseModel):
    """Structured market intelligence result from AI."""

    crop: str
    current_market_trend: Literal["UP", "DOWN", "STABLE"]
    price_outlook: str
    recommended_action: Literal["SELL_NOW", "HOLD", "WAIT"]
    best_selling_window_days: int = Field(..., ge=0)
    expected_profit_change_percent: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reasoning: str
    farmer_advice: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class MarketIntelligenceResponse(BaseModel):
    """API response wrapper for market intelligence."""

    success: bool
    crop: str
    region: Optional[str]
    analysis: MarketIntelligenceResult
