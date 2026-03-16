# app/schemas/assessment.py

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class Reason(BaseModel):
    """
    A single factor contributing to the overall safety score.
    """
    code: str = Field(..., description="Short identifier for the risk or mitigation factor.")
    message: str = Field(..., description="Human-readable explanation of the factor.")
    weight: int = Field(..., description="Numerical impact on the risk score (+ risk, - mitigation).")


class Recommendation(BaseModel):
    """
    A user-friendly recommendation based on the computed safety verdict.
    """
    message: str = Field(..., description="Actionable advice for the user.")


class SafetyAssessment(BaseModel):
    """
    The complete Wi‑Fi safety assessment model returned by the unified endpoint.

    This model is highly explainable and transparent:
    - verdict:    'safe', 'caution', or 'unsafe'
    - score:      integer 0–100
    - reasons:    list of weighted contributing factors
    - recommendations: practical tips for safe usage
    - context:    extra metadata for UI or debugging
    """
    wifi_id: str = Field(..., description="Identifier of the matched hotspot from the database.")
    bssid: str = Field(...,
                       description="BSSID used for the assessment (may be 'unknown' when using SSID-only resolution).")

    verdict: str = Field(..., description="Final classification: safe / caution / unsafe.")
    score: int = Field(..., ge=0, le=100, description="0–100 composite risk score (higher = riskier).")

    reasons: List[Reason] = Field(
        default_factory=list,
        description="List of weighted risk and mitigation factors."
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Actions the user can take to improve safety."
    )

    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata such as security mode, crime count, location, status, and distance."
    )