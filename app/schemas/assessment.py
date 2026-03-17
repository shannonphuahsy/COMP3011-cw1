from typing import List, Dict, Any
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # ✔️ REQUIRED for Pydantic v2


class Reason(BaseModel):
    code: str = Field(..., description="Short identifier for the risk or mitigation factor.")
    message: str = Field(..., description="Human-readable explanation of the factor.")
    weight: int = Field(..., description="Numerical impact on the risk score (+ risk, - mitigation).")


class Recommendation(BaseModel):
    message: str = Field(..., description="Actionable advice for the user.")


class SafetyAssessment(BaseModel):
    """
    The complete Wi‑Fi safety assessment model returned by the unified endpoint.
    """

    # ⭐⭐ THE IMPORTANT PART — allows risk_score and other extra fields ⭐⭐
    model_config = ConfigDict(extra="allow")

    wifi_id: str = Field(..., description="Identifier of the matched hotspot from the database.")
    bssid: str = Field(..., description="BSSID used for the assessment.")

    verdict: str = Field(..., description="Final classification: safe / caution / unsafe.")
    score: int = Field(..., ge=0, le=100, description="0–100 composite risk score.")

    reasons: List[Reason] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)