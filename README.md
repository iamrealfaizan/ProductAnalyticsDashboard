# Product Analytics Dashboard - MVP

This repository contains a working MVP based on `PRD.md`.

## What is implemented
- FastAPI backend for event ingestion and analytics APIs
- SQLite event storage for quick local setup
- Core KPIs: DAU, WAU, MAU, total events
- Feature adoption analytics
- Cohort retention analytics (Day 0..N)
- Streamlit dashboard with interactive charts
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
- `GET /analytics/summary`
- `GET /analytics/dau?days=30`
- `GET /analytics/feature-adoption?days=30`
- `GET /analytics/retention?max_days=7`
- `GET /health`

## Example Event Payload
```json
{
  "user_id": "123",
  "event_name": "feature_click",
  "timestamp": "2026-04-07T12:00:00Z",
  "metadata": {
    "feature": "resume_analysis"
  }
}
```

## Notes
- MVP is intentionally simple and optimized for local development.
- For production: move to Postgres/ClickHouse, add auth, pre-aggregations, queue/stream ingestion, and alerting.
