from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import ProductEvent


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _apply_time_filters(stmt, date_from: str | None = None, date_to: str | None = None):
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    if start is not None:
        stmt = stmt.where(ProductEvent.timestamp >= start)
    if end is not None:
        stmt = stmt.where(ProductEvent.timestamp <= end)
    return stmt


def _safe_round(value: float) -> float:
    return round(float(value), 2)


def get_dau_series(
    db: Session,
    days: int = 14,
    event_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    end_day = datetime.utcnow().date()
    start_day = end_day - timedelta(days=days - 1)

    stmt = select(func.date(ProductEvent.timestamp), func.count(func.distinct(ProductEvent.user_id)))
    stmt = stmt.where(ProductEvent.timestamp >= datetime.combine(start_day, datetime.min.time()))
    if event_name:
        stmt = stmt.where(ProductEvent.event_name == event_name)

    stmt = _apply_time_filters(stmt, date_from=date_from, date_to=date_to)
    stmt = stmt.group_by(func.date(ProductEvent.timestamp)).order_by(func.date(ProductEvent.timestamp))

    rows = db.execute(stmt).all()
    by_day = {str(day): count for day, count in rows}

    output = []
    for i in range(days):
        day_value = start_day + timedelta(days=i)
        day_key = day_value.isoformat()
        output.append({"date": day_key, "dau": by_day.get(day_key, 0)})
    return output


def get_summary_kpis(
    db: Session,
    event_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    now = datetime.utcnow()
    day_start = datetime(now.year, now.month, now.day)
    week_start = day_start - timedelta(days=7)
    month_start = day_start - timedelta(days=30)

    total_stmt = select(func.count(ProductEvent.id))
    if event_name:
        total_stmt = total_stmt.where(ProductEvent.event_name == event_name)
    total_stmt = _apply_time_filters(total_stmt, date_from=date_from, date_to=date_to)
    total_events = db.execute(total_stmt).scalar_one() or 0

    def active_users_since(since: datetime) -> int:
        stmt = select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= since)
        if event_name:
            stmt = stmt.where(ProductEvent.event_name == event_name)
        stmt = _apply_time_filters(stmt, date_from=date_from, date_to=date_to)
        return db.execute(stmt).scalar_one() or 0

    dau = active_users_since(day_start)
    wau = active_users_since(week_start)
    mau = active_users_since(month_start)

    session_metrics = get_session_summary(db, days=30, event_name=event_name, date_from=date_from, date_to=date_to)

    return {
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "total_events": total_events,
        "avg_session_duration_minutes": session_metrics["avg_session_duration_minutes"],
        "avg_events_per_session": session_metrics["avg_events_per_session"],
    }


def get_feature_adoption(
    db: Session,
    days: int = 30,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    since = datetime.utcnow() - timedelta(days=days)

    total_users_stmt = select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= since)
    total_users_stmt = _apply_time_filters(total_users_stmt, date_from=date_from, date_to=date_to)
    total_users = db.execute(total_users_stmt).scalar_one() or 1

    stmt = (
        select(ProductEvent.event_name, func.count(func.distinct(ProductEvent.user_id)))
        .where(ProductEvent.timestamp >= since)
        .group_by(ProductEvent.event_name)
        .order_by(func.count(func.distinct(ProductEvent.user_id)).desc())
    )
    stmt = _apply_time_filters(stmt, date_from=date_from, date_to=date_to)

    rows = db.execute(stmt).all()
    output = []
    for feature, unique_users in rows:
        rate = _safe_round((unique_users / total_users) * 100)
        output.append({"feature": feature, "unique_users": unique_users, "adoption_rate": rate})
    return output


def get_retention(
    db: Session,
    max_days: int = 7,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    user_first_seen_stmt = select(ProductEvent.user_id, func.min(func.date(ProductEvent.timestamp))).group_by(
        ProductEvent.user_id
    )
    user_first_seen_stmt = _apply_time_filters(user_first_seen_stmt, date_from=date_from, date_to=date_to)
    first_seen_rows = db.execute(user_first_seen_stmt).all()

    cohort_map = {user_id: str(first_day) for user_id, first_day in first_seen_rows}
    cohort_sizes = defaultdict(int)
    for cohort_day in cohort_map.values():
        cohort_sizes[cohort_day] += 1

    all_events_stmt = select(ProductEvent.user_id, func.date(ProductEvent.timestamp))
    all_events_stmt = _apply_time_filters(all_events_stmt, date_from=date_from, date_to=date_to)
    all_events = db.execute(all_events_stmt).all()

    retained = defaultdict(set)
    for user_id, active_day in all_events:
        cohort_day = cohort_map.get(user_id)
        if not cohort_day:
            continue
        day_n = (date.fromisoformat(str(active_day)) - date.fromisoformat(cohort_day)).days
        if 0 <= day_n <= max_days:
            retained[(cohort_day, day_n)].add(user_id)

    result = []
    for (cohort_day, day_n), users in sorted(retained.items()):
        size = cohort_sizes.get(cohort_day, 1)
        result.append(
            {
                "cohort_date": cohort_day,
                "day_n": day_n,
                "retained_users": len(users),
                "retention_rate": _safe_round((len(users) / size) * 100),
            }
        )
    return result


def get_user_segments(
    db: Session,
    days: int = 30,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    end_day = datetime.utcnow().date()
    start_day = end_day - timedelta(days=days - 1)

    first_seen_stmt = select(ProductEvent.user_id, func.min(func.date(ProductEvent.timestamp))).group_by(
        ProductEvent.user_id
    )
    first_seen_stmt = _apply_time_filters(first_seen_stmt, date_from=date_from, date_to=date_to)
    first_seen = {user_id: str(first_day) for user_id, first_day in db.execute(first_seen_stmt).all()}

    activity_stmt = select(func.date(ProductEvent.timestamp), ProductEvent.user_id).where(
        ProductEvent.timestamp >= datetime.combine(start_day, datetime.min.time())
    )
    activity_stmt = _apply_time_filters(activity_stmt, date_from=date_from, date_to=date_to)
    activity = db.execute(activity_stmt).all()

    day_users: dict[str, set[str]] = defaultdict(set)
    for active_day, user_id in activity:
        day_users[str(active_day)].add(user_id)

    output = []
    for i in range(days):
        current = start_day + timedelta(days=i)
        day_key = current.isoformat()
        users = day_users.get(day_key, set())
        new_users = sum(1 for user in users if first_seen.get(user) == day_key)
        total_users = len(users)
        output.append(
            {
                "date": day_key,
                "new_users": new_users,
                "returning_users": max(total_users - new_users, 0),
                "total_users": total_users,
            }
        )
    return output


def get_session_summary(
    db: Session,
    days: int = 30,
    event_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    since = datetime.utcnow() - timedelta(days=days)

    stmt = select(ProductEvent.user_id, ProductEvent.metadata_json).where(ProductEvent.timestamp >= since)
    if event_name:
        stmt = stmt.where(ProductEvent.event_name == event_name)
    stmt = _apply_time_filters(stmt, date_from=date_from, date_to=date_to)
    rows = db.execute(stmt).all()

    sessions: dict[str, dict] = {}
    fallback_counter = 0
    for user_id, metadata in rows:
        metadata = metadata or {}
        session_id = metadata.get("session_id")
        if not session_id:
            fallback_counter += 1
            session_id = f"fallback_{user_id}_{fallback_counter}"
        duration = float(metadata.get("session_duration_seconds", 0) or 0)

        session = sessions.setdefault(session_id, {"user_id": user_id, "events": 0, "duration": 0.0})
        session["events"] += 1
        if duration > session["duration"]:
            session["duration"] = duration

    total_sessions = len(sessions)
    if total_sessions == 0:
        return {
            "period_days": days,
            "total_sessions": 0,
            "avg_session_duration_minutes": 0.0,
            "avg_events_per_session": 0.0,
            "avg_sessions_per_user": 0.0,
        }

    total_duration = sum(item["duration"] for item in sessions.values())
    total_events = sum(item["events"] for item in sessions.values())
    unique_users = len({item["user_id"] for item in sessions.values()}) or 1

    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "avg_session_duration_minutes": _safe_round((total_duration / 60) / total_sessions),
        "avg_events_per_session": _safe_round(total_events / total_sessions),
        "avg_sessions_per_user": _safe_round(total_sessions / unique_users),
    }


def get_funnel(
    db: Session,
    steps: list[str],
    days: int = 30,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    if not steps:
        return []

    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(ProductEvent.user_id, ProductEvent.event_name).where(ProductEvent.timestamp >= since)
    stmt = stmt.where(ProductEvent.event_name.in_(steps))
    stmt = _apply_time_filters(stmt, date_from=date_from, date_to=date_to)

    rows = db.execute(stmt).all()
    users_by_step: dict[str, set[str]] = {step: set() for step in steps}
    for user_id, event_name in rows:
        users_by_step[event_name].add(user_id)

    first_count = len(users_by_step.get(steps[0], set()))
    output = []
    previous_count = first_count
    for step in steps:
        current_count = len(users_by_step.get(step, set()))
        conversion_prev = _safe_round((current_count / previous_count) * 100) if previous_count else 0.0
        conversion_first = _safe_round((current_count / first_count) * 100) if first_count else 0.0
        output.append(
            {
                "step": step,
                "unique_users": current_count,
                "conversion_from_previous_pct": conversion_prev,
                "conversion_from_first_pct": conversion_first,
            }
        )
        previous_count = current_count
    return output


def get_churn(
    db: Session,
    inactivity_days: int = 14,
    lookback_days: int = 30,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    now = datetime.utcnow()
    lookback_start = now - timedelta(days=lookback_days)
    inactive_since = now - timedelta(days=inactivity_days)

    lookback_stmt = select(ProductEvent.user_id).where(ProductEvent.timestamp >= lookback_start)
    lookback_stmt = _apply_time_filters(lookback_stmt, date_from=date_from, date_to=date_to)
    lookback_users = {row[0] for row in db.execute(lookback_stmt).all()}

    active_stmt = select(ProductEvent.user_id).where(ProductEvent.timestamp >= inactive_since)
    active_stmt = _apply_time_filters(active_stmt, date_from=date_from, date_to=date_to)
    active_users = {row[0] for row in db.execute(active_stmt).all()}

    churned = lookback_users - active_users
    return {
        "churned_users": len(churned),
        "at_risk_users": max(len(lookback_users) - len(active_users), 0),
        "inactivity_days": inactivity_days,
        "lookback_days": lookback_days,
    }
