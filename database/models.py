# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class JobPosting(Base):
    __tablename__ = "job_postings"

    id              = Column(Integer, primary_key=True)
    source          = Column(String)          # linkedin, indeed, etc.
    title           = Column(String)
    company         = Column(String)
    location        = Column(String)
    job_type        = Column(String)          # remote, hybrid, onsite
    seniority       = Column(String)          # junior, mid, senior
    salary_min      = Column(Integer)
    salary_max      = Column(Integer)
    description     = Column(Text)
    skills          = Column(JSON)            # ["Python", "SQL", ...]
    url             = Column(String, unique=True)
    posted_at       = Column(DateTime)
    scraped_at      = Column(DateTime, default=datetime.utcnow)
    raw_html        = Column(Text)            # preserve original

class RunLog(Base):
    __tablename__ = "run_logs"

    id              = Column(Integer, primary_key=True)
    run_at          = Column(DateTime, default=datetime.utcnow)
    jobs_found      = Column(Integer)
    jobs_new        = Column(Integer)
    jobs_failed     = Column(Integer)
    sources         = Column(JSON)
    duration_secs   = Column(Integer)