from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_EVENT_NAMES = {
    "page_view",
    "signup",
    "feature_click",
    "resume_analysis",
    "export_pdf",
    "api_usage",
    "error",
}


class EventIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    event_name: str = Field(min_length=1, max_length=128)
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:
        if value not in ALLOWED_EVENT_NAMES:
            allowed = ", ".join(sorted(ALLOWED_EVENT_NAMES))
            raise ValueError(f"Unsupported event_name '{value}'. Allowed: {allowed}")
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("metadata must be an object")
        return value


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    event_name: str
    timestamp: datetime
    metadata: dict


class DAUPoint(BaseModel):
    date: str
    dau: int


class FeatureAdoptionPoint(BaseModel):
    feature: str
    unique_users: int
    adoption_rate: float


class RetentionPoint(BaseModel):
    cohort_date: str
    day_n: int
    retained_users: int
    retention_rate: float


class UserSegmentPoint(BaseModel):
    date: str
    new_users: int
    returning_users: int
    total_users: int


class SessionSummary(BaseModel):
    period_days: int
    total_sessions: int
    avg_session_duration_minutes: float
    avg_events_per_session: float
    avg_sessions_per_user: float


class FunnelStepPoint(BaseModel):
    step: str
    unique_users: int
    conversion_from_previous_pct: float
    conversion_from_first_pct: float


class ChurnPoint(BaseModel):
    churned_users: int
    at_risk_users: int
    inactivity_days: int
    lookback_days: int
