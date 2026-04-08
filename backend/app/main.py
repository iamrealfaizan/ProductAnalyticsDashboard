from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import ProductEvent
from .schemas import DAUPoint, EventIn, FeatureAdoptionPoint, RetentionPoint
from .services import get_dau_series, get_feature_adoption, get_retention, get_summary_kpis

app = FastAPI(title="Product Analytics Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/events")
def ingest_event(payload: EventIn, db: Session = Depends(get_db)) -> dict:
    event = ProductEvent(
        user_id=payload.user_id,
        event_name=payload.event_name,
        timestamp=payload.timestamp,
        metadata_json=payload.metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "user_id": event.user_id,
        "event_name": event.event_name,
        "timestamp": event.timestamp.isoformat(),
        "metadata": event.metadata_json,
    }


@app.get("/analytics/dau", response_model=list[DAUPoint])
def analytics_dau(days: int = Query(default=14, ge=1, le=365), db: Session = Depends(get_db)):
    return get_dau_series(db, days=days)


@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    return get_summary_kpis(db)


@app.get("/analytics/feature-adoption", response_model=list[FeatureAdoptionPoint])
def analytics_feature_adoption(
    days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)
):
    return get_feature_adoption(db, days=days)


@app.get("/analytics/retention", response_model=list[RetentionPoint])
def analytics_retention(
    max_days: int = Query(default=7, ge=1, le=30), db: Session = Depends(get_db)
):
    return get_retention(db, max_days=max_days)
