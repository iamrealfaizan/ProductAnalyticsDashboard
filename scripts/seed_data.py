import random
import uuid
from datetime import UTC, datetime, timedelta

import requests

API = "http://127.0.0.1:8000"
EVENT_NAMES = [
    "page_view",
    "signup",
    "feature_click",
    "resume_analysis",
    "export_pdf",
    "api_usage",
    "error",
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
    active_users = random.sample(users, random.randint(60, 160))
    for user in active_users:
        session_count = random.randint(1, 3)
        for _ in range(session_count):
            session_id = str(uuid.uuid4())
            session_duration_seconds = random.randint(120, 3600)
            event_count = random.randint(2, 8)

            event_chain = ["page_view"]
            if random.random() < 0.45:
                event_chain.append("signup")
            if random.random() < 0.7:
                event_chain.append("feature_click")
            if random.random() < 0.55:
                event_chain.append("resume_analysis")
            if random.random() < 0.4:
                event_chain.append("export_pdf")

            remaining = max(event_count - len(event_chain), 0)
            for _ in range(remaining):
                event_chain.append(random.choice(EVENT_NAMES))

            random.shuffle(event_chain)
            for event_name in event_chain:
                event_time = day + timedelta(minutes=random.randint(0, 1439))
                payload = {
                    "user_id": user,
                    "event_name": event_name,
                    "timestamp": event_time.isoformat(),
                    "metadata": {
                        "feature": random.choice(["search", "analysis", "export", "share", "onboarding"]),
                        "session_id": session_id,
                        "session_duration_seconds": session_duration_seconds,
                        "is_error": event_name == "error",
                    },
                }
                response = session.post(f"{API}/events", json=payload, timeout=5)
                response.raise_for_status()
                count += 1

print(f"Seeded events successfully: {count} events")
