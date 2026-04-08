from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import ProductEvent


def utc_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.replace(tzinfo=None), end.replace(tzinfo=None)


def get_dau_series(db: Session, days: int = 14) -> list[dict]:
    today = datetime.utcnow().date()
    start_day = today - timedelta(days=days - 1)

    stmt = (
        select(func.date(ProductEvent.timestamp), func.count(func.distinct(ProductEvent.user_id)))
        .where(ProductEvent.timestamp >= datetime.combine(start_day, datetime.min.time()))
        .group_by(func.date(ProductEvent.timestamp))
        .order_by(func.date(ProductEvent.timestamp))
    )

    rows = db.execute(stmt).all()
    by_day = {str(day): count for day, count in rows}

    output = []
    for i in range(days):
        d = start_day + timedelta(days=i)
        output.append({"date": d.isoformat(), "dau": by_day.get(d.isoformat(), 0)})
    return output


def get_active_users(db: Session, days: int) -> int:
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= since)
    return db.execute(stmt).scalar_one() or 0


def get_summary_kpis(db: Session) -> dict:
    now = datetime.utcnow()
    day_start = datetime(now.year, now.month, now.day)
    week_start = day_start - timedelta(days=7)
    month_start = day_start - timedelta(days=30)

    total_events = db.execute(select(func.count(ProductEvent.id))).scalar_one() or 0
    dau = db.execute(
        select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= day_start)
    ).scalar_one() or 0

    wau = db.execute(
        select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= week_start)
    ).scalar_one() or 0

    mau = db.execute(
        select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= month_start)
    ).scalar_one() or 0

    avg_session_duration_minutes = 0.0

    return {
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "total_events": total_events,
        "avg_session_duration_minutes": avg_session_duration_minutes,
    }


def get_feature_adoption(db: Session, days: int = 30) -> list[dict]:
    since = datetime.utcnow() - timedelta(days=days)

    total_users_stmt = select(func.count(func.distinct(ProductEvent.user_id))).where(ProductEvent.timestamp >= since)
    total_users = db.execute(total_users_stmt).scalar_one() or 1

    stmt = (
        select(ProductEvent.event_name, func.count(func.distinct(ProductEvent.user_id)))
        .where(ProductEvent.timestamp >= since)
        .group_by(ProductEvent.event_name)
        .order_by(func.count(func.distinct(ProductEvent.user_id)).desc())
    )

    rows = db.execute(stmt).all()
    output = []
    for feature, unique_users in rows:
        rate = round((unique_users / total_users) * 100, 2)
        output.append({"feature": feature, "unique_users": unique_users, "adoption_rate": rate})
    return output


def get_retention(db: Session, max_days: int = 7) -> list[dict]:
    user_first_seen_stmt = (
        select(ProductEvent.user_id, func.min(func.date(ProductEvent.timestamp)))
        .group_by(ProductEvent.user_id)
    )
    first_seen_rows = db.execute(user_first_seen_stmt).all()

    cohort_map = {user_id: str(first_day) for user_id, first_day in first_seen_rows}
    cohort_sizes = defaultdict(int)
    for cohort_day in cohort_map.values():
        cohort_sizes[cohort_day] += 1

    all_events_stmt = select(ProductEvent.user_id, func.date(ProductEvent.timestamp))
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
                "retention_rate": round((len(users) / size) * 100, 2),
            }
        )
    return result
