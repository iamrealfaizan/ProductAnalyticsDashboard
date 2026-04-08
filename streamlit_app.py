import time
from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Product Analytics Dashboard", page_icon=":bar_chart:", layout="wide")

st.title("Product Analytics Dashboard")
st.caption("MVP analytics dashboard aligned with PRD v1.0")

API_BASE = st.sidebar.text_input("API Base URL", value="http://127.0.0.1:8000")
lookback_days = st.sidebar.slider("Lookback Days", min_value=7, max_value=90, value=30, step=1)
selected_event = st.sidebar.selectbox(
    "Event Filter",
    options=["all", "page_view", "signup", "feature_click", "resume_analysis", "export_pdf", "api_usage", "error"],
)

col_from, col_to = st.sidebar.columns(2)
date_from = col_from.date_input("From", value=None)
date_to = col_to.date_input("To", value=None)

max_retention_days = st.sidebar.slider("Retention Window (days)", min_value=3, max_value=30, value=7, step=1)
inactivity_days = st.sidebar.slider("Churn Inactivity Days", min_value=3, max_value=60, value=14, step=1)

funnel_steps = st.sidebar.text_input(
    "Funnel Steps (comma-separated)", value="page_view,signup,feature_click,resume_analysis,export_pdf"
)

auto_refresh = st.sidebar.checkbox("Auto Refresh", value=False)
refresh_seconds = st.sidebar.slider("Refresh every (seconds)", min_value=5, max_value=60, value=15, step=5)


def _serialize_date(value):
    if value is None:
        return None
    return value.isoformat()


def _base_params() -> dict:
    params = {
        "date_from": _serialize_date(date_from),
        "date_to": _serialize_date(date_to),
    }
    if selected_event != "all":
        params["event_name"] = selected_event
    return {k: v for k, v in params.items() if v is not None}


def fetch(path: str, params: dict | None = None):
    url = f"{API_BASE}{path}"
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


try:
    params = _base_params()

    summary = fetch("/analytics/summary", params=params)
    dau_series = fetch("/analytics/dau", {**params, "days": lookback_days})
    feature_adoption = fetch("/analytics/feature-adoption", {"days": lookback_days, "date_from": params.get("date_from"), "date_to": params.get("date_to")})
    retention = fetch(
        "/analytics/retention",
        {
            "max_days": max_retention_days,
            "date_from": params.get("date_from"),
            "date_to": params.get("date_to"),
        },
    )
    user_segments = fetch(
        "/analytics/user-segments",
        {
            "days": lookback_days,
            "date_from": params.get("date_from"),
            "date_to": params.get("date_to"),
        },
    )
    sessions = fetch("/analytics/sessions", {**params, "days": lookback_days})
    funnel = fetch(
        "/analytics/funnel",
        {
            "steps": funnel_steps,
            "days": lookback_days,
            "date_from": params.get("date_from"),
            "date_to": params.get("date_to"),
        },
    )
    churn = fetch(
        "/analytics/churn",
        {
            "inactivity_days": inactivity_days,
            "lookback_days": lookback_days,
            "date_from": params.get("date_from"),
            "date_to": params.get("date_to"),
        },
    )
except Exception as exc:
    st.error(f"Failed to fetch analytics data: {exc}")
    st.stop()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("DAU", summary.get("dau", 0))
k2.metric("WAU", summary.get("wau", 0))
k3.metric("MAU", summary.get("mau", 0))
k4.metric("Total Events", summary.get("total_events", 0))
k5.metric("Avg Session (min)", summary.get("avg_session_duration_minutes", 0.0))
k6.metric("Events / Session", summary.get("avg_events_per_session", 0.0))

st.subheader("Daily Active Users")
dau_df = pd.DataFrame(dau_series)
if not dau_df.empty:
    dau_df["date"] = pd.to_datetime(dau_df["date"])
    fig_dau = px.line(dau_df, x="date", y="dau", markers=True)
    st.plotly_chart(fig_dau, use_container_width=True)
else:
    st.info("No DAU data available yet.")

st.subheader("New vs Returning Users")
segment_df = pd.DataFrame(user_segments)
if not segment_df.empty:
    segment_long = segment_df.melt(id_vars=["date"], value_vars=["new_users", "returning_users"], var_name="segment", value_name="users")
    segment_long["date"] = pd.to_datetime(segment_long["date"])
    fig_segment = px.bar(segment_long, x="date", y="users", color="segment", barmode="stack")
    st.plotly_chart(fig_segment, use_container_width=True)
else:
    st.info("No segment data available yet.")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Feature Adoption")
    feature_df = pd.DataFrame(feature_adoption)
    if not feature_df.empty:
        fig_feature = px.bar(feature_df, x="feature", y="adoption_rate", text="adoption_rate")
        fig_feature.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        st.plotly_chart(fig_feature, use_container_width=True)
    else:
        st.info("No feature adoption data available yet.")

with c2:
    st.subheader("Funnel Conversion")
    funnel_df = pd.DataFrame(funnel)
    if not funnel_df.empty:
        fig_funnel = px.funnel(funnel_df, x="unique_users", y="step")
        st.plotly_chart(fig_funnel, use_container_width=True)
        st.dataframe(funnel_df, use_container_width=True)
    else:
        st.info("No funnel data available yet.")

st.subheader("Retention Cohorts")
ret_df = pd.DataFrame(retention)
if not ret_df.empty:
    pivot = ret_df.pivot(index="cohort_date", columns="day_n", values="retention_rate").fillna(0)
    fig_heat = px.imshow(
        pivot,
        labels={"x": "Day N", "y": "Cohort Date", "color": "Retention %"},
        text_auto=True,
        aspect="auto",
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No retention data available yet.")

s1, s2, s3 = st.columns(3)
s1.metric("Total Sessions", sessions.get("total_sessions", 0))
s2.metric("Avg Sessions / User", sessions.get("avg_sessions_per_user", 0.0))
s3.metric("Churned Users", churn.get("churned_users", 0))

st.subheader("Live Event Ingestion Test")
with st.form("ingest_form", clear_on_submit=True):
    user_id = st.text_input("User ID", value="user_123")
    event_name = st.selectbox(
        "Event Name",
        options=["page_view", "signup", "feature_click", "resume_analysis", "export_pdf", "api_usage", "error"],
    )
    feature_name = st.text_input("Feature", value="resume_analysis")
    session_id = st.text_input("Session ID", value="session_demo_001")
    session_duration = st.number_input("Session Duration (seconds)", min_value=0, value=300, step=30)
    submitted = st.form_submit_button("Send Event")

if submitted:
    payload = {
        "user_id": user_id,
        "event_name": event_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "metadata": {
            "feature": feature_name,
            "session_id": session_id,
            "session_duration_seconds": session_duration,
            "is_error": event_name == "error",
        },
    }
    try:
        response = requests.post(f"{API_BASE}/events", json=payload, timeout=10)
        response.raise_for_status()
        st.success("Event ingested successfully")
        st.json(response.json())
    except Exception as exc:
        st.error(f"Event ingestion failed: {exc}")

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()
