from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Product Analytics Dashboard", page_icon=":bar_chart:", layout="wide")
API_BASE = st.sidebar.text_input("API Base URL", value="http://127.0.0.1:8000")

st.title("Product Analytics Dashboard")
st.caption("MVP analytics dashboard aligned with PRD v1.0")


def fetch(path: str, params: dict | None = None):
    url = f"{API_BASE}{path}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


try:
    summary = fetch("/analytics/summary")
    dau_series = fetch("/analytics/dau", {"days": 30})
    feature_adoption = fetch("/analytics/feature-adoption", {"days": 30})
    retention = fetch("/analytics/retention", {"max_days": 7})
except Exception as exc:
    st.error(f"Failed to fetch analytics data: {exc}")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("DAU", summary.get("dau", 0))
col2.metric("WAU", summary.get("wau", 0))
col3.metric("MAU", summary.get("mau", 0))
col4.metric("Total Events", summary.get("total_events", 0))

st.subheader("Daily Active Users (30 days)")
dau_df = pd.DataFrame(dau_series)
if not dau_df.empty:
    dau_df["date"] = pd.to_datetime(dau_df["date"])
    fig_dau = px.line(dau_df, x="date", y="dau", markers=True)
    st.plotly_chart(fig_dau, use_container_width=True)
else:
    st.info("No DAU data available yet.")

st.subheader("Feature Adoption")
feature_df = pd.DataFrame(feature_adoption)
if not feature_df.empty:
    fig_feature = px.bar(feature_df, x="feature", y="adoption_rate", text="adoption_rate")
    fig_feature.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    st.plotly_chart(fig_feature, use_container_width=True)
else:
    st.info("No feature adoption data available yet.")

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

st.subheader("Live Event Ingestion Test")
with st.form("ingest_form", clear_on_submit=True):
    user_id = st.text_input("User ID", value="user_123")
    event_name = st.text_input("Event Name", value="feature_click")
    feature_name = st.text_input("Feature", value="resume_analysis")
    submitted = st.form_submit_button("Send Event")

if submitted:
    payload = {
        "user_id": user_id,
        "event_name": event_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "metadata": {"feature": feature_name},
    }
    try:
        response = requests.post(f"{API_BASE}/events", json=payload, timeout=10)
        response.raise_for_status()
        st.success("Event ingested successfully")
        st.json(response.json())
    except Exception as exc:
        st.error(f"Event ingestion failed: {exc}")
