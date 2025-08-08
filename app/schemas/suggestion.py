from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SuggestionBase(BaseModel):
    """Base schema for suggestion data."""
    query_id: UUID = Field(..., description="ID of the associated query")
    suggestion_type: str = Field(..., description="Type of suggestion (e.g., 'INDEX', 'QUERY_REWRITE')")
    message: str = Field(..., description="Human-readable suggestion message")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    source: str = Field(..., description="Source of suggestion (e.g., 'RULE_ENGINE', 'ML_MODEL')")
    estimated_improvement_ms: Optional[float] = Field(None, description="Estimated time improvement in milliseconds")
    implementation_cost: Optional[str] = Field(None, description="Implementation cost ('LOW', 'MEDIUM', 'HIGH')")


class SuggestionCreate(SuggestionBase):
    """Schema for creating a new suggestion entry."""
    pass


class SuggestionResponse(SuggestionBase):
    """Schema for suggestion response."""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class SuggestionList(BaseModel):
    """Schema for list of suggestions."""
    suggestions: list[SuggestionResponse]
    query_id: UUID
    total: int


class PredictionRequest(BaseModel):
    """Schema for ML prediction request."""
    query_text: str = Field(..., description="SQL query text")
    features: dict[str, float] = Field(..., description="Query features for prediction")


class PredictionResponse(BaseModel):
    """Schema for ML prediction response."""
    predicted_time_ms: float = Field(..., description="Predicted execution time in milliseconds")
    confidence: float = Field(..., description="Prediction confidence score")
    suggestions: list[SuggestionResponse] = Field(default_factory=list, description="Generated suggestions") 