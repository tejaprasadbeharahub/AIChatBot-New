"""
One-time script to create market_intelligence table on Supabase
and advance the alembic_version stamp.
"""
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.db.base import Base
from app.models.market_intelligence import MarketIntelligence  # noqa: F401

NEW_REVISION = "m0n1o2p3q4r5"
OLD_REVISION = "l9m0n1o2p3q4"


def main() -> None:
    url = settings.supabase_database_url
    if not url:
        raise RuntimeError("SUPABASE_DATABASE_URL is not set in .env")

    print(f"Connecting to Supabase... ({url[:30]}...)")
    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 15})

    Base.metadata.create_all(engine, tables=[Base.metadata.tables["market_intelligence"]])
    print("Table created: market_intelligence")

    with engine.connect() as conn:
        conn.execute(
            text("UPDATE alembic_version SET version_num = :new WHERE version_num = :old"),
            {"new": NEW_REVISION, "old": OLD_REVISION},
        )
        conn.commit()
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        print("alembic_version:", [r[0] for r in rows])

    engine.dispose()
    print("Done.")


if __name__ == "__main__":
    main()
