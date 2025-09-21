import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    must_have = Column(Text)
    good_to_have = Column(Text)
    qualifications = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    branch_office = Column(String, nullable=True)
    state = Column(String, nullable=True)
    evaluations = relationship("Evaluation", back_populates="job")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    resume_path = Column(String, nullable=True)
    resume_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    city = Column(String, nullable=True) # New field
    state = Column(String, nullable=True) # New field
    evaluations = relationship("Evaluation", back_populates="candidate")

class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    score = Column(Float)
    verdict = Column(String)
    hard_score = Column(Float)
    semantic_score = Column(Float)
    missing_skills = Column(Text)
    feedback = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    job = relationship("Job", back_populates="evaluations")
    candidate = relationship("Candidate", back_populates="evaluations")