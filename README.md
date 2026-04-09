# Product Analytics Dashboard

## Table of Contents
1. [What This Project Is](#what-this-project-is)
2. [Purpose and Vision](#purpose-and-vision)
3. [Problem We Solve](#problem-we-solve)
4. [Unique Selling Proposition (USP)](#unique-selling-proposition-usp)
5. [Why This Is Better Than Typical Alternatives](#why-this-is-better-than-typical-alternatives)
6. [Who This Is For](#who-this-is-for)
7. [What You Can Do With It](#what-you-can-do-with-it)
8. [How It Works (End-to-End)](#how-it-works-end-to-end)
9. [Tech Stack](#tech-stack)
10. [Project Structure](#project-structure)
11. [Data Model and Event Schema](#data-model-and-event-schema)
12. [Analytics and Functionalities Explained](#analytics-and-functionalities-explained)
13. [API Reference](#api-reference)
14. [Complete Setup and Run Guide (Start to Finish)](#complete-setup-and-run-guide-start-to-finish)
15. [How an End User Uses This in Real Life](#how-an-end-user-uses-this-in-real-life)
16. [Operational Tips and Best Practices](#operational-tips-and-best-practices)
17. [Troubleshooting](#troubleshooting)
18. [FAQ](#faq)

---

## What This Project Is
Product Analytics Dashboard is an end-to-end analytics product that captures user behavior events, processes analytics metrics, and visualizes product performance in an interactive dashboard.

It includes:
- A backend API for ingesting and querying analytics data.
- A persistent event store.
- A live dashboard for business and product insights.
- Seed tooling to generate realistic sample usage data.

This repository is built as a practical MVP+ that demonstrates real product analytics workflows and can be used for demos, learning, and early-stage internal analytics.

---

## Purpose and Vision
The goal is to help teams make better product decisions by turning raw user interactions into understandable, actionable insights.

Vision:
- Move from guesswork to data-backed product decisions.
- Provide both historical and near real-time visibility.
- Keep the system simple enough for rapid iteration while still being extensible for production-scale evolution.

---

## Problem We Solve
Most teams face one or more of these issues:
- User behavior data exists, but is scattered or hard to analyze quickly.
- Decision-makers need simple dashboards, not raw logs or SQL queries.
- Teams lack fast feedback loops for adoption, retention, and engagement.
- Analytics setup is often too heavy, expensive, or slow for early-stage needs.

This project solves that by providing a lightweight but meaningful analytics platform that gives immediate clarity on:
- Who is active?
- Which features are being used?
- Where users drop off in journeys?
- How retention changes over time?
- Which users are at risk of churn?

---

## Unique Selling Proposition (USP)
1. Complete analytics loop in one project
From event ingestion to retention/funnel/churn dashboards, everything is integrated.

2. Business-friendly + engineer-friendly
Product managers can read dashboard KPIs directly, while engineers get clean APIs and extensible services.

3. Real-world metrics, not toy counters
Includes DAU/WAU/MAU, feature adoption, cohorts, funnel, sessions, and churn.

4. Fast local startup
Runs locally with SQLite and Streamlit, enabling quick demos and zero infra complexity.

5. Designed for growth
Architecture and code organization allow transition to larger stacks (Postgres/ClickHouse, streaming, auth, alerts).

---

## Why This Is Better Than Typical Alternatives
Compared with spreadsheets/manual reporting:
- Automated ingestion and metrics computation.
- Live, filterable visualizations.
- Reproducible analytics logic.

Compared with heavy enterprise analytics tools (for MVP stage):
- Lower setup overhead.
- Easier customization for your product events.
- Full ownership of data model and metric definitions.

Compared with ad-hoc scripts:
- API-first architecture.
- Structured schema validation.
- UI and analytics logic already wired end-to-end.

Important note:
This project is optimized as a practical MVP+ foundation, not as a direct drop-in replacement for full enterprise analytics platforms with massive scale and multi-tenant governance.

---

## Who This Is For
Primary users:
- Product Managers
- Founders
- Growth teams

Secondary users:
- Engineers
- Data Analysts

Use cases:
- Monitor activation and engagement health.
- Track feature adoption over time.
- Evaluate retention cohorts.
- Analyze funnel conversion drop-offs.
- Identify churn risk segments.

---

## What You Can Do With It
- Ingest events from product interactions.
- View summary KPIs (DAU, WAU, MAU, total events).
- Analyze daily active trends.
- Segment users into new vs returning.
- Measure feature adoption rates.
- Visualize retention as cohort heatmaps.
- Measure session behavior (duration/events/sessions per user).
- Track funnel step conversions.
- Estimate churn based on inactivity windows.
- Test ingestion live from the dashboard form.

---

## How It Works (End-to-End)
1. A user interacts with your product.
2. Your app sends an event to `POST /events`.
3. FastAPI validates schema and stores the event in SQLite.
4. Analytics endpoints aggregate data by time window and dimensions.
5. Streamlit dashboard fetches endpoint data and renders interactive visualizations.
6. Product stakeholders use the visuals to make product decisions.

---

## Tech Stack
Backend:
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

Data store:
- SQLite (local, simple, fast iteration)

Frontend/dashboard:
- Streamlit
- Plotly
- Pandas

Utilities:
- Requests (API communication and seed script)

---

## Project Structure
- `backend/app/main.py`: API routes, app initialization, endpoint wiring.
- `backend/app/services.py`: analytics computation logic.
- `backend/app/models.py`: SQLAlchemy models.
- `backend/app/schemas.py`: request/response validation and typing.
- `backend/app/database.py`: DB engine/session and index setup.
- `streamlit_app.py`: dashboard UX and visualization.
- `scripts/seed_data.py`: synthetic data generation for demos/testing.
- `requirements.txt`: dependency list.
- `PRD.md`: product requirements and roadmap intent.

---

## Data Model and Event Schema
Core event schema:
```json
{
  "user_id": "string",
  "event_name": "string",
  "timestamp": "datetime",
  "metadata": {}
}
```

Current supported event names:
- `page_view`
- `signup`
- `feature_click`
- `resume_analysis`
- `export_pdf`
- `api_usage`
- `error`

Recommended metadata fields:
- `feature`: feature identifier
- `session_id`: session correlation id
- `session_duration_seconds`: approximate session duration
- `is_error`: boolean error flag for error events

---

## Analytics and Functionalities Explained
### 1. Summary KPIs
Endpoint: `GET /analytics/summary`
- DAU: unique users active in last 1 day.
- WAU: unique users active in last 7 days.
- MAU: unique users active in last 30 days.
- Total events: all ingested events in selected filter context.
- Session-derived quality metrics.

### 2. DAU Trend
Endpoint: `GET /analytics/dau`
- Plots daily active users across a chosen window.
- Useful for engagement trend and campaign impact checks.

### 3. Feature Adoption
Endpoint: `GET /analytics/feature-adoption`
- Shows percentage of active users touching each event/feature.
- Useful for prioritizing product improvements.

### 4. Retention Cohorts
Endpoint: `GET /analytics/retention`
- Groups users by first seen date.
- Shows retention Day 0..N as heatmap values.

### 5. User Segmentation (New vs Returning)
Endpoint: `GET /analytics/user-segments`
- Daily split of first-time vs repeat active users.
- Helps track acquisition quality and habit formation.

### 6. Session Analytics
Endpoint: `GET /analytics/sessions`
- Total sessions.
- Average session duration.
- Average events per session.
- Average sessions per user.

### 7. Funnel Conversion
Endpoint: `GET /analytics/funnel`
- Configurable ordered steps.
- Shows user counts and conversion percentages across journey.

### 8. Churn
Endpoint: `GET /analytics/churn`
- Estimates churned/at-risk users based on inactivity and lookback windows.

### 9. Live Ingestion Form
In dashboard:
- Lets users submit events directly.
- Useful for testing instrumentation instantly.

---

## API Reference
### Health
- `GET /health`

### Event ingestion
- `POST /events`

### Analytics
- `GET /analytics/summary`
- `GET /analytics/dau?days=30`
- `GET /analytics/feature-adoption?days=30`
- `GET /analytics/retention?max_days=7`
- `GET /analytics/user-segments?days=30`
- `GET /analytics/sessions?days=30`
- `GET /analytics/funnel?steps=page_view,signup,feature_click`
- `GET /analytics/churn?inactivity_days=14&lookback_days=30`

Common optional query params on several endpoints:
- `date_from=YYYY-MM-DD`
- `date_to=YYYY-MM-DD`
- `event_name=<event>`

---

## Complete Setup and Run Guide (Start to Finish)
### Prerequisites
- Python 3.10+ recommended.
- Git installed.
- Windows/macOS/Linux terminal access.

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd ProductAnalysisDashboard
```

### 2. Create virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start backend API
```bash
uvicorn backend.app.main:app --reload
```

Backend URLs:
- API base: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

### 5. Seed demo data (optional but recommended)
Open a second terminal (with same virtual environment activated):
```bash
python scripts/seed_data.py
```

If successful, you will see seeded event count.

### 6. Start dashboard
In second terminal:
```bash
streamlit run streamlit_app.py
```

Dashboard URL (usually):
- `http://localhost:8501`

### 7. Verify everything is working
- Open API docs and call `/health`.
- Open dashboard and confirm KPI cards are populated.
- Submit an event through Live Event Ingestion form.

### 8. Daily usage workflow
1. Keep backend running.
2. Open dashboard.
3. Set filters (lookback, date, event type).
4. Review KPIs and charts.
5. Export/share insights manually with team.

---

## How an End User Uses This in Real Life
This section is written for product stakeholders.

### Scenario: Product Manager reviewing weekly product health
1. Open dashboard URL.
2. Choose `Lookback Days = 30`.
3. Check KPI row:
- If DAU grows but MAU is flat, recent activation may be volatile.
- If events/session drops, engagement quality may be weakening.
4. Open New vs Returning chart:
- If new users rise but returning users lag, onboarding may be good but stickiness weak.
5. Open Feature Adoption:
- Identify high and low adoption features.
- Cross-check roadmap priorities.
6. Open Funnel:
- Detect biggest conversion drop (e.g., `signup -> feature_click`).
- Prioritize UX fixes for that step.
7. Open Retention heatmap:
- Observe if recent cohorts retain better/worse than older cohorts.
8. Open Churn metric:
- If churned users rise, define win-back actions.
9. Use Live Event form only for testing instrumentation, not production event capture.

### Scenario: Founder preparing investor update
- Use KPI + retention + funnel trend to explain product health narrative.
- Use date filters to compare before/after release windows.
- Highlight adoption uplift for newly launched feature.

### Scenario: Growth team validating campaign impact
- Filter dates across campaign period.
- Track DAU and signup movement.
- Validate whether top-of-funnel growth converts to deeper actions.

---

## Operational Tips and Best Practices
1. Event naming consistency
- Keep event names standardized and documented.

2. Metadata hygiene
- Always include `session_id` for better session analytics quality.

3. Date filter discipline
- Compare equivalent windows (e.g., last 7 days vs previous 7 days) for fair interpretation.

4. Keep demo and production separate
- Use this local setup for development and demos.
- For production, migrate to robust databases and deployment stack.

5. Define metric ownership
- Align PM/data/engineering teams on exact KPI definitions to avoid reporting mismatch.

---

## Troubleshooting
### `ModuleNotFoundError` when running commands
Cause: wrong Python interpreter.
Fix: activate `.venv` and rerun command.

### `No module named 'app'`
Cause: wrong uvicorn module path.
Fix: run from project root using:
```bash
uvicorn backend.app.main:app --reload
```

### Seed script says backend not reachable
Cause: backend not running.
Fix: start backend first, then run seed script.

### Dashboard shows fetch errors
Check:
- Backend is running at `http://127.0.0.1:8000`
- Streamlit sidebar API URL matches backend URL
- No firewall/proxy blocking localhost

### PowerShell blocks script activation
Try:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## FAQ
### 1. Is this production ready?
It is production-inspired but optimized for MVP/local usage. For production, add stronger security, scaling database, observability, CI/CD, and infrastructure hardening.

### 2. Can non-technical users use the dashboard?
Yes. The dashboard is built for product and business users to consume insights without writing code.

### 3. Do I need to seed data every time?
No. Seed once for demo data. Rerun only when you want refreshed synthetic datasets.

### 4. Why SQLite for now?
SQLite is simple and fast for local iteration. It reduces setup friction and helps focus on product logic first.

### 5. How do we move to a larger database later?
Swap DB config and ORM models to Postgres/ClickHouse path, add migrations, and optionally pre-aggregation tables.

### 6. Can I add custom events?
Yes. Update allowed event names and instrumentation conventions, then ingest events via `/events`.

### 7. What are the key decisions this dashboard helps with?
Feature prioritization, onboarding optimization, retention improvement, and churn mitigation.

### 8. How real-time is it?
Near real-time. Data appears quickly after ingestion; dashboard also supports auto-refresh.

### 9. Can I use this with my existing product/app?
Yes. Send your app events to the ingestion endpoint using the defined schema.

### 10. What should we implement next?
High-value next steps: alerting, custom metrics builder, auth/RBAC, production DB migration, test automation, and anomaly detection.

---

If you are evaluating this project for product or engineering interviews, focus on this narrative:
- It demonstrates end-to-end product analytics ownership.
- It combines product thinking with implementation rigor.
- It is immediately usable, and it has a clear path to production maturity.
----------------------------------------------------------------------------
