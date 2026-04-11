import io
import json
import time
import zipfile
from datetime import UTC, date, datetime, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Product Analytics Dashboard", page_icon=":bar_chart:", layout="wide")

st.title("Product Analytics Dashboard")
st.caption("MVP analytics dashboard aligned with PRD v1.0")

EVENT_OPTIONS = ["all", "page_view", "signup", "feature_click", "resume_analysis", "export_pdf", "api_usage", "error"]
DEFAULT_PRESETS = {
    "Last 7 Days": {"lookback_days": 7, "selected_event": "all"},
    "Last 30 Days": {"lookback_days": 30, "selected_event": "all"},
    "Activation Funnel": {"lookback_days": 30, "selected_event": "signup"},
    "Error Monitoring": {"lookback_days": 14, "selected_event": "error"},
}

if "custom_presets" not in st.session_state:
    st.session_state.custom_presets = {}
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0


def _serialize_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _base_params(selected_event: str, date_from: date | None, date_to: date | None) -> dict:
    params = {"date_from": _serialize_date(date_from), "date_to": _serialize_date(date_to)}
    if selected_event != "all":
        params["event_name"] = selected_event
    return {k: v for k, v in params.items() if v is not None}


def _safe_pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


def _period_bounds(lookback_days: int, date_from: date | None, date_to: date | None) -> tuple[date, date]:
    if date_from and date_to:
        return date_from, date_to
    if date_from and not date_to:
        return date_from, date.today()
    if date_to and not date_from:
        return date_to - timedelta(days=lookback_days - 1), date_to
    end_day = date.today()
    start_day = end_day - timedelta(days=lookback_days - 1)
    return start_day, end_day


def _previous_period(start_day: date, end_day: date) -> tuple[date, date]:
    period_days = (end_day - start_day).days + 1
    previous_end = start_day - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period_days - 1)
    return previous_start, previous_end


def fetch(api_base: str, path: str, params: dict | None = None):
    url = f"{api_base}{path}"
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def _empty_state(message: str):
    st.info(f"{message} Adjust date range/event filter or ingest more events from the form below.")


with st.sidebar:
    API_BASE = st.text_input("API Base URL", value="http://127.0.0.1:8000")

    all_presets = {**DEFAULT_PRESETS, **st.session_state.custom_presets}
    preset_name = st.selectbox("Quick Presets", options=["None", *all_presets.keys()])
    preset_apply = st.button("Apply Preset", use_container_width=True)

    lookback_days = st.slider("Lookback Days", min_value=7, max_value=90, value=30, step=1, key="lookback_days")
    selected_event = st.selectbox("Event Filter", options=EVENT_OPTIONS, key="selected_event")

    col_from, col_to = st.columns(2)
    date_from = col_from.date_input("From", value=None, key="date_from")
    date_to = col_to.date_input("To", value=None, key="date_to")

    max_retention_days = st.slider("Retention Window (days)", min_value=3, max_value=30, value=7, step=1)
    inactivity_days = st.slider("Churn Inactivity Days", min_value=3, max_value=60, value=14, step=1)

    funnel_steps = st.text_input(
        "Funnel Steps (comma-separated)", value="page_view,signup,feature_click,resume_analysis,export_pdf"
    )

    compare_period = st.checkbox("Compare With Previous Period", value=True)
    auto_refresh = st.checkbox("Auto Refresh", value=False)
    refresh_seconds = st.slider("Refresh every (seconds)", min_value=5, max_value=60, value=15, step=5)

    st.markdown("### Save Current Preset")
    preset_save_name = st.text_input("Preset Name", value="")
    preset_save_clicked = st.button("Save Preset", use_container_width=True)

if preset_apply and preset_name != "None":
    selected_preset = all_presets[preset_name]
    st.session_state.lookback_days = selected_preset.get("lookback_days", 30)
    st.session_state.selected_event = selected_preset.get("selected_event", "all")
    st.session_state.date_from = selected_preset.get("date_from")
    st.session_state.date_to = selected_preset.get("date_to")
    st.rerun()

if preset_save_clicked:
    name = preset_save_name.strip()
    if not name:
        st.warning("Enter a preset name before saving.")
    else:
        st.session_state.custom_presets[name] = {
            "lookback_days": lookback_days,
            "selected_event": selected_event,
            "date_from": date_from,
            "date_to": date_to,
        }
        st.success(f"Saved preset '{name}'.")

current_start, current_end = _period_bounds(lookback_days, date_from, date_to)
previous_start, previous_end = _previous_period(current_start, current_end)
params = _base_params(selected_event, date_from, date_to)
last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"Last updated: {last_updated}")

try:
    summary = fetch(API_BASE, "/analytics/summary", params=params)
    dau_series = fetch(API_BASE, "/analytics/dau", {**params, "days": lookback_days})
    feature_adoption = fetch(
        API_BASE,
        "/analytics/feature-adoption",
        {"days": lookback_days, "date_from": params.get("date_from"), "date_to": params.get("date_to")},
    )
    retention = fetch(
        API_BASE,
        "/analytics/retention",
        {"max_days": max_retention_days, "date_from": params.get("date_from"), "date_to": params.get("date_to")},
    )
    user_segments = fetch(
        API_BASE,
        "/analytics/user-segments",
        {"days": lookback_days, "date_from": params.get("date_from"), "date_to": params.get("date_to")},
    )
    sessions = fetch(API_BASE, "/analytics/sessions", {**params, "days": lookback_days})
    funnel = fetch(
        API_BASE,
        "/analytics/funnel",
        {"steps": funnel_steps, "days": lookback_days, "date_from": params.get("date_from"), "date_to": params.get("date_to")},
    )
    churn = fetch(
        API_BASE,
        "/analytics/churn",
        {
            "inactivity_days": inactivity_days,
            "lookback_days": lookback_days,
            "date_from": params.get("date_from"),
            "date_to": params.get("date_to"),
        },
    )
    previous_summary = {}
    if compare_period:
        previous_summary = fetch(
            API_BASE,
            "/analytics/summary",
            {
                "date_from": previous_start.isoformat(),
                "date_to": previous_end.isoformat(),
                **({"event_name": selected_event} if selected_event != "all" else {}),
            },
        )
except Exception as exc:
    st.error(f"Failed to fetch analytics data: {exc}")
    st.stop()


def _delta(label: str, current: float, previous: float | None) -> tuple[str, str | None]:
    if previous is None:
        return str(current), None
    delta_pct = _safe_pct_change(current, previous)
    return str(current), f"{delta_pct:+.1f}% vs prev"


k1, k2, k3, k4, k5, k6 = st.columns(6)
prev = previous_summary if previous_summary else None

v, d = _delta("DAU", summary.get("dau", 0), prev.get("dau", 0) if prev else None)
k1.metric("DAU", v, d)
v, d = _delta("WAU", summary.get("wau", 0), prev.get("wau", 0) if prev else None)
k2.metric("WAU", v, d)
v, d = _delta("MAU", summary.get("mau", 0), prev.get("mau", 0) if prev else None)
k3.metric("MAU", v, d)
v, d = _delta("Total Events", summary.get("total_events", 0), prev.get("total_events", 0) if prev else None)
k4.metric("Total Events", v, d)
v, d = _delta(
    "Avg Session (min)",
    round(summary.get("avg_session_duration_minutes", 0.0), 2),
    prev.get("avg_session_duration_minutes", 0.0) if prev else None,
)
k5.metric("Avg Session (min)", v, d)
v, d = _delta(
    "Events / Session",
    round(summary.get("avg_events_per_session", 0.0), 2),
    prev.get("avg_events_per_session", 0.0) if prev else None,
)
k6.metric("Events / Session", v, d)

st.subheader("Daily Active Users")
dau_df = pd.DataFrame(dau_series)
if not dau_df.empty:
    dau_df["date"] = pd.to_datetime(dau_df["date"])
    fig_dau = px.line(dau_df, x="date", y="dau", markers=True)
    st.plotly_chart(fig_dau, use_container_width=True)
else:
    _empty_state("No DAU data available.")

st.subheader("New vs Returning Users")
segment_df = pd.DataFrame(user_segments)
if not segment_df.empty:
    segment_long = segment_df.melt(
        id_vars=["date"], value_vars=["new_users", "returning_users"], var_name="segment", value_name="users"
    )
    segment_long["date"] = pd.to_datetime(segment_long["date"])
    fig_segment = px.bar(segment_long, x="date", y="users", color="segment", barmode="stack")
    st.plotly_chart(fig_segment, use_container_width=True)
else:
    _empty_state("No segment data available.")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Feature Adoption")
    feature_df = pd.DataFrame(feature_adoption)
    if not feature_df.empty:
        fig_feature = px.bar(feature_df, x="feature", y="adoption_rate", text="adoption_rate")
        fig_feature.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        st.plotly_chart(fig_feature, use_container_width=True)
    else:
        _empty_state("No feature adoption data available.")

with c2:
    st.subheader("Funnel Conversion")
    funnel_df = pd.DataFrame(funnel)
    if not funnel_df.empty:
        fig_funnel = px.funnel(funnel_df, x="unique_users", y="step")
        st.plotly_chart(fig_funnel, use_container_width=True)
        st.dataframe(funnel_df, use_container_width=True)
        if len(funnel_df) > 1:
            drop_candidates = funnel_df.iloc[1:].copy()
            weakest = drop_candidates.loc[drop_candidates["conversion_from_previous_pct"].idxmin()]
            drop_pct = max(100 - float(weakest["conversion_from_previous_pct"]), 0)
            st.warning(
                f"Biggest funnel drop-off: '{weakest['step']}' ({drop_pct:.1f}% drop from previous step)."
            )
    else:
        _empty_state("No funnel data available.")

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
    _empty_state("No retention data available.")

s1, s2, s3 = st.columns(3)
s1.metric("Total Sessions", sessions.get("total_sessions", 0))
s2.metric("Avg Sessions / User", sessions.get("avg_sessions_per_user", 0.0))
s3.metric("Churned Users", churn.get("churned_users", 0))

st.subheader("Alerts & Insights")
with st.expander("Configure Alerts", expanded=False):
    alert_dau_drop_threshold = st.slider("DAU Drop Alert Threshold (%)", 5, 90, 20, 5)
    alert_churn_threshold = st.number_input("Churned Users Alert Threshold", min_value=1, value=50, step=1)
    alert_funnel_min_conversion = st.slider("Minimum Funnel Step Conversion (%)", 5, 100, 50, 5)

alerts = []
if prev and summary.get("dau", 0) < prev.get("dau", 0):
    dau_drop_pct = -_safe_pct_change(summary.get("dau", 0), prev.get("dau", 0))
    if dau_drop_pct >= alert_dau_drop_threshold:
        alerts.append(f"DAU dropped by {dau_drop_pct:.1f}% vs previous period.")

if churn.get("churned_users", 0) >= alert_churn_threshold:
    alerts.append(f"Churned users reached {churn.get('churned_users', 0)} (threshold {alert_churn_threshold}).")

if "funnel_df" in locals() and not funnel_df.empty and len(funnel_df) > 1:
    min_step_conv = float(funnel_df.iloc[1:]["conversion_from_previous_pct"].min())
    if min_step_conv < alert_funnel_min_conversion:
        alerts.append(f"Funnel step conversion fell to {min_step_conv:.1f}% (threshold {alert_funnel_min_conversion}%).")

if alerts:
    for alert in alerts:
        st.error(alert)
else:
    st.success("No alerts triggered for current thresholds.")

st.subheader("Export Current View")
export_frames = {
    "summary.json": pd.DataFrame([summary]),
    "dau.csv": pd.DataFrame(dau_series),
    "feature_adoption.csv": pd.DataFrame(feature_adoption),
    "retention.csv": pd.DataFrame(retention),
    "user_segments.csv": pd.DataFrame(user_segments),
    "sessions.csv": pd.DataFrame([sessions]),
    "funnel.csv": pd.DataFrame(funnel),
    "churn.csv": pd.DataFrame([churn]),
}

buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
    snapshot = {
        "exported_at": datetime.now(UTC).isoformat(),
        "filters": {
            "lookback_days": lookback_days,
            "selected_event": selected_event,
            "date_from": _serialize_date(date_from),
            "date_to": _serialize_date(date_to),
            "compare_previous_period": compare_period,
        },
        "summary": summary,
        "previous_summary": previous_summary if prev else None,
    }
    bundle.writestr("snapshot.json", json.dumps(snapshot, indent=2))
    for filename, frame in export_frames.items():
        if filename.endswith(".json"):
            bundle.writestr(filename, frame.to_json(orient="records", indent=2))
        else:
            bundle.writestr(filename, frame.to_csv(index=False))

st.download_button(
    "Download Current View (ZIP)",
    data=buffer.getvalue(),
    file_name=f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
    mime="application/zip",
    use_container_width=True,
)

st.subheader("Live Event Ingestion Test")
with st.form("ingest_form", clear_on_submit=True):
    user_id = st.text_input("User ID", value="user_123")
    event_name = st.selectbox(
        "Event Name", options=["page_view", "signup", "feature_click", "resume_analysis", "export_pdf", "api_usage", "error"]
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
    st.session_state.refresh_counter += 1
    time.sleep(refresh_seconds)
    st.rerun()
