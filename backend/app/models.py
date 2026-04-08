from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ProductEvent(Base):
    __tablename__ = "product_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    event_name: Mapped[str] = mapped_column(String(128), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
