from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from database.models import Base

# Configure engine. For SQLite, enable check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes tables in database and applies lightweight idempotent schema migrations."""
    Base.metadata.create_all(bind=engine)

    if not DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Nytt';"))
                conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(100);"))
                conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS candidate_name VARCHAR(150);"))
                conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS notes TEXT;"))
                conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP;"))
                conn.commit()
        except Exception:
            pass


def get_db():
    """Generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
