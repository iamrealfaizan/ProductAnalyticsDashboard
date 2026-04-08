from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    event_name: str = Field(min_length=1, max_length=128)
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)


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
