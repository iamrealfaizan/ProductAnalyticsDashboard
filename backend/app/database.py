from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./analytics.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_indexes() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_product_events_user_time ON product_events (user_id, timestamp)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_product_events_event_time ON product_events (event_name, timestamp)"
            )
        )
