from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from database.models import Base

# Configure engine with robust pooling
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes tables in database and applies lightweight idempotent schema migrations."""
    Base.metadata.create_all(bind=engine)

    if not DATABASE_URL.startswith("sqlite"):
        statements = [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Nytt';",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(100);",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS candidate_name VARCHAR(150);",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS notes TEXT;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_recruitment_agency BOOLEAN DEFAULT FALSE;",
            "CREATE INDEX IF NOT EXISTS ix_leads_is_recruitment_agency ON leads(is_recruitment_agency);",
            """
            UPDATE leads 
            SET is_recruitment_agency = TRUE 
            WHERE is_recruitment_agency IS NOT TRUE AND (
                company_name ILIKE '%academic work%' OR
                company_name ILIKE '%randstad%' OR
                company_name ILIKE '%adecco%' OR
                company_name ILIKE '%manpower%' OR
                company_name ILIKE '%experis%' OR
                company_name ILIKE '%bravura%' OR
                company_name ILIKE '%studentconsulting%' OR
                company_name ILIKE '%student consulting%' OR
                company_name ILIKE '%framtiden%' OR
                company_name ILIKE '%poolia%' OR
                company_name ILIKE '%clockwork%' OR
                company_name ILIKE '%tng %' OR company_name ILIKE '%tng group%' OR
                company_name ILIKE '%jefferson wells%' OR
                company_name ILIKE '%dedicare%' OR
                company_name ILIKE '%sjr %' OR
                company_name ILIKE '%michael page%' OR
                company_name ILIKE '%page personnel%' OR
                company_name ILIKE '%hays%' OR
                company_name ILIKE '%ants tech%' OR
                company_name ILIKE '%wise it%' OR company_name ILIKE '%wise professional%' OR
                company_name ILIKE '%worko%' OR
                company_name ILIKE '%centric%' OR
                company_name ILIKE '%hero rekrytering%' OR
                company_name ILIKE '%maxkompetens%' OR
                company_name ILIKE '%onepartnergroup%' OR
                company_name ILIKE '%lernia%' OR
                company_name ILIKE '%perido%' OR
                company_name ILIKE '%clevry%' OR
                company_name ILIKE '%wrknest%' OR
                company_name ILIKE '%bemannia%' OR
                company_name ILIKE '%uniflex%' OR
                company_name ILIKE '%montico%' OR
                company_name ILIKE '%wikan personal%' OR
                company_name ILIKE '%skill scandinavia%' OR
                company_name ILIKE '%skill ab%' OR
                company_name ILIKE '%skill rekrytering%' OR
                LOWER(TRIM(company_name)) = 'skill'
            );
            """,
            "ALTER TABLE market_features ADD COLUMN IF NOT EXISTS policy_rate FLOAT;",
            "ALTER TABLE market_features ADD COLUMN IF NOT EXISTS policy_rate_lag3m FLOAT;",
            "ALTER TABLE market_features ADD COLUMN IF NOT EXISTS business_confidence_it FLOAT;",
            "ALTER TABLE market_features ADD COLUMN IF NOT EXISTS layoff_notices INTEGER;",
        ]
        for stmt in statements:
            try:
                with engine.begin() as conn:
                    conn.execute(text(stmt))
            except Exception:
                pass


def get_db():
    """Generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
