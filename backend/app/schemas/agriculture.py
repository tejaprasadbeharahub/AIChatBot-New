from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AgricultureDiagnosisRequest(BaseModel):
    """Farmer query for crop disease diagnosis."""

    query: str = Field(..., description="Description of symptoms or problem observed")
    crop_type: Optional[str] = Field(None, description="Type of crop (e.g., wheat, rice, tomato)")
    region: Optional[str] = Field(None, description="Region or state in India")
    weather: Optional[str] = Field(None, description="Current weather conditions")
    soil_type: Optional[str] = Field(None, description="Soil type if known")
    symptoms: Optional[str] = Field(None, description="Additional specific symptoms")

    @field_validator("query", mode="before")
    @classmethod
    def validate_query(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("query must be a string")
        value = value.strip()
        if len(value) < 5:
            raise ValueError("query must be at least 5 characters")
        return value


class AgricultureDiagnosisResult(BaseModel):
    """Structured crop disease diagnosis from AI."""

    disease_name: str
    scientific_name: Optional[str] = None
    affected_parts: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    urgency_level: str
    symptoms_matched: list[str] = Field(default_factory=list)
    likely_causes: list[str] = Field(default_factory=list)
    treatment_steps: list[str] = Field(default_factory=list)
    organic_solutions: list[str] = Field(default_factory=list)
    chemical_solutions: list[str] = Field(default_factory=list)
    preventive_measures: list[str] = Field(default_factory=list)
    best_season_to_act: Optional[str] = None
    additional_notes: Optional[str] = None


class AgricultureDiagnosisResponse(BaseModel):
    """API response wrapper for crop diagnosis."""

    success: bool
    crop_type: Optional[str]
    region: Optional[str]
    diagnosis: AgricultureDiagnosisResult
