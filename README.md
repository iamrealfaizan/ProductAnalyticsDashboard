# Product Analytics Dashboard - MVP+

This repository contains a working product analytics dashboard based on `PRD.md`, now extended with segmentation, sessions, funnels, and churn analytics.

## What is implemented
- FastAPI backend for event ingestion and analytics APIs
- SQLite event storage for quick local setup
- Core KPIs: DAU, WAU, MAU, total events
- New vs returning user segmentation
- Feature adoption analytics
- Cohort retention analytics (Day 0..N)
- Session analytics (avg duration, events/session, sessions/user)
- Funnel analytics with configurable steps
- Churn analytics based on inactivity window
- Streamlit dashboard with interactive charts + filters
- Sample seed script for realistic test data

## Project Structure
- `backend/app/main.py` - FastAPI app and routes
- `backend/app/models.py` - SQLAlchemy models
- `backend/app/services.py` - analytics computation logic
- `streamlit_app.py` - Streamlit dashboard UI
- `scripts/seed_data.py` - sample data generator

## Run Locally
1. Create and activate virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start backend API:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
4. (Optional) Seed sample data:
   ```bash
   python scripts/seed_data.py
   ```
5. Start dashboard:
   ```bash
   streamlit run streamlit_app.py
   ```

## API Endpoints
- `POST /events`
- `GET /health`
- `GET /analytics/summary`
- `GET /analytics/dau?days=30`
- `GET /analytics/feature-adoption?days=30`
- `GET /analytics/retention?max_days=7`
- `GET /analytics/user-segments?days=30`
- `GET /analytics/sessions?days=30`
- `GET /analytics/funnel?steps=page_view,signup,feature_click`
- `GET /analytics/churn?inactivity_days=14&lookback_days=30`

## Example Event Payload
```json
{
  "user_id": "123",
  "event_name": "feature_click",
  "timestamp": "2026-04-07T12:00:00Z",
  "metadata": {
    "feature": "resume_analysis",
    "session_id": "session_001",
    "session_duration_seconds": 420
  }
}
```

## Notes
- MVP is intentionally simple and optimized for local development.
- For production: move to Postgres/ClickHouse, add auth, pre-aggregations, queue/stream ingestion, and alerting.
