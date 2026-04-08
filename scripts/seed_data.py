import random
from datetime import UTC, datetime, timedelta

import requests

API = "http://127.0.0.1:8000"
EVENT_NAMES = [
    "page_view",
    "signup",
    "feature_click",
    "resume_analysis",
    "export_pdf",
]

users = [f"user_{i:03d}" for i in range(1, 201)]

session = requests.Session()

try:
    health = session.get(f"{API}/health", timeout=5)
    health.raise_for_status()
except requests.RequestException as exc:
    raise SystemExit(f"Backend is not reachable at {API}. Start uvicorn first. Details: {exc}") from exc

count = 0
for day_offset in range(30):
    day = datetime.now(UTC) - timedelta(days=day_offset)
    active_users = random.sample(users, random.randint(50, 150))
    for user in active_users:
        for _ in range(random.randint(1, 5)):
            event = {
                "user_id": user,
                "event_name": random.choice(EVENT_NAMES),
                "timestamp": (day + timedelta(minutes=random.randint(0, 1439))).isoformat(),
                "metadata": {"feature": random.choice(["search", "analysis", "export", "share"])},
            }
            response = session.post(f"{API}/events", json=event, timeout=5)
            response.raise_for_status()
            count += 1

print(f"Seeded events successfully: {count} events")
