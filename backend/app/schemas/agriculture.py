from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class AgricultureDiagnosisRequest(BaseModel):
    """Farmer query for crop disease diagnosis."""

    query: str = Field(..., description="Description of symptoms or problem observed")
    crop_type: Optional[str] = Field(None, description="Type of crop (e.g., wheat, rice, tomato)")
    region: Optional[str] = Field(None, description="Region or state in India")
    location: Optional[str] = Field(None, description="Location alias used by external workflows")
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


class FarmQuerySubmissionRequest(BaseModel):
    """Public farm query submission payload from frontend."""

    farmer_id: Optional[str] = Field(None, description="Farmer identifier (ignored; backend uses static value)")
    query: str = Field(..., description="Farmer query text")
    crop_type: Optional[str] = Field(None, description="Type of crop")
    location: Optional[str] = Field(None, description="Farmer location")
    weather: Optional[str] = Field(None, description="Weather conditions")

    @field_validator("query", mode="before")
    @classmethod
    def validate_submission_query(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("query must be a string")
        value = value.strip()
        if len(value) < 5:
            raise ValueError("query must be at least 5 characters")
        return value


class FarmQuerySubmissionResponse(BaseModel):
    """Response returned after forwarding farm query to N8N webhook."""

    success: bool
    message: str
    submitted_payload: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None


class FarmCurrentQueryResponse(BaseModel):
    """Latest available farm query initial request details."""

    success: bool
    source: str
    record_id: str
    created_at: datetime
    initial_input: dict[str, Any]
