from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, ensure_indexes
from .models import ProductEvent
from .schemas import (
    ChurnPoint,
    DAUPoint,
    EventIn,
    FeatureAdoptionPoint,
    FunnelStepPoint,
    RetentionPoint,
    SessionSummary,
    UserSegmentPoint,
)
from .services import (
    get_churn,
    get_dau_series,
    get_feature_adoption,
    get_funnel,
    get_retention,
    get_session_summary,
    get_summary_kpis,
    get_user_segments,
)

app = FastAPI(title="Product Analytics Dashboard API", version="1.1.0")

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
ensure_indexes()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/events")
def ingest_event(payload: EventIn, db: Session = Depends(get_db)) -> dict:
    duplicate_stmt = (
        select(ProductEvent)
        .where(ProductEvent.user_id == payload.user_id)
        .where(ProductEvent.event_name == payload.event_name)
        .where(ProductEvent.timestamp == payload.timestamp.replace(tzinfo=None))
    )
    existing = db.execute(duplicate_stmt).scalar_one_or_none()
    if existing:
        return {
            "id": existing.id,
            "user_id": existing.user_id,
            "event_name": existing.event_name,
            "timestamp": existing.timestamp.isoformat(),
            "metadata": existing.metadata_json,
            "deduplicated": True,
        }

    event = ProductEvent(
        user_id=payload.user_id,
        event_name=payload.event_name,
        timestamp=payload.timestamp.replace(tzinfo=None),
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
        "deduplicated": False,
    }


@app.get("/analytics/dau", response_model=list[DAUPoint])
def analytics_dau(
    days: int = Query(default=14, ge=1, le=365),
    event_name: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_dau_series(db, days=days, event_name=event_name, date_from=date_from, date_to=date_to)


@app.get("/analytics/summary")
def analytics_summary(
    event_name: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_summary_kpis(db, event_name=event_name, date_from=date_from, date_to=date_to)


@app.get("/analytics/feature-adoption", response_model=list[FeatureAdoptionPoint])
def analytics_feature_adoption(
    days: int = Query(default=30, ge=1, le=365),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_feature_adoption(db, days=days, date_from=date_from, date_to=date_to)


@app.get("/analytics/retention", response_model=list[RetentionPoint])
def analytics_retention(
    max_days: int = Query(default=7, ge=1, le=30),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_retention(db, max_days=max_days, date_from=date_from, date_to=date_to)


@app.get("/analytics/user-segments", response_model=list[UserSegmentPoint])
def analytics_user_segments(
    days: int = Query(default=30, ge=1, le=365),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_user_segments(db, days=days, date_from=date_from, date_to=date_to)


@app.get("/analytics/sessions", response_model=SessionSummary)
def analytics_sessions(
    days: int = Query(default=30, ge=1, le=365),
    event_name: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_session_summary(db, days=days, event_name=event_name, date_from=date_from, date_to=date_to)


@app.get("/analytics/funnel", response_model=list[FunnelStepPoint])
def analytics_funnel(
    steps: str = Query(default="page_view,signup,feature_click,resume_analysis,export_pdf"),
    days: int = Query(default=30, ge=1, le=365),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    parsed_steps = [step.strip() for step in steps.split(",") if step.strip()]
    return get_funnel(db, steps=parsed_steps, days=days, date_from=date_from, date_to=date_to)


@app.get("/analytics/churn", response_model=ChurnPoint)
def analytics_churn(
    inactivity_days: int = Query(default=14, ge=1, le=365),
    lookback_days: int = Query(default=30, ge=1, le=365),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_churn(
        db,
        inactivity_days=inactivity_days,
        lookback_days=lookback_days,
        date_from=date_from,
        date_to=date_to,
    )
