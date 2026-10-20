from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association Table for Many-to-Many relationship between Leads and Skills
lead_skills = Table(
    "lead_skills",
    Base.metadata,
    Column("lead_id", Integer, ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, default="General")

    leads = relationship("Lead", secondary=lead_skills, back_populates="skills")

    def __repr__(self):
        return f"<Skill {self.name} ({self.category})>"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)  # "jobtech" or "brainville"
    external_id = Column(String(200), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    company_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(100), nullable=True, index=True)
    municipality_code = Column(String(20), nullable=True)
    region = Column(String(100), default="Östergötland")
    url = Column(String(500), nullable=True)
    is_consultant_assignment = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint per external source ID
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
    )

    skills = relationship("Skill", secondary=lead_skills, back_populates="leads")

    def __repr__(self):
        return f"<Lead {self.title} at {self.company_name} ({self.source})>"

