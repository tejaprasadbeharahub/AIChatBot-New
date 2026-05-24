"""
One-time script to create workflow + agriculture tables on Supabase
and stamp the alembic_version table.
"""
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.db.base import Base
from app.models.workflow_request import WorkflowRequest  # noqa: F401
from app.models.research_result import ResearchResult  # noqa: F401
from app.models.daily_report import DailyReport  # noqa: F401
from app.models.crop_diagnosis import CropDiagnosis  # noqa: F401

TARGET_TABLES = ["workflow_requests", "research_results", "daily_reports", "crop_diagnoses"]
REVISION = "l9m0n1o2p3q4"


def main() -> None:
    url = settings.supabase_database_url
    if not url:
        raise RuntimeError("SUPABASE_DATABASE_URL is not set in .env")

    print(f"Connecting to Supabase... ({url[:30]}...)")
    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 15})

    # Create only the 4 tables
    tables = [Base.metadata.tables[t] for t in TARGET_TABLES]
    Base.metadata.create_all(engine, tables=tables)
    print("Tables created:", TARGET_TABLES)

    # Stamp alembic_version
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
        conn.execute(text(
            "INSERT INTO alembic_version (version_num) VALUES (:v) ON CONFLICT DO NOTHING"
        ), {"v": REVISION})
        conn.commit()
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        print("alembic_version:", [r[0] for r in rows])

    engine.dispose()
    print("Done.")


if __name__ == "__main__":
    main()
