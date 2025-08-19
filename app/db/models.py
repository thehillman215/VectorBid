from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Index
from .database import Base


class Pilot(Base):
    __tablename__ = "pilots"

    pilot_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True)
    ctx_id = Column(String, index=True)
    pilot_id = Column(String, ForeignKey("pilots.pilot_id"), index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RulePack(Base):
    __tablename__ = "rule_packs"

    id = Column(Integer, primary_key=True)
    ctx_id = Column(String, index=True)
    airline = Column(String, index=True)
    version = Column(String)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BidPackage(Base):
    __tablename__ = "bid_packages"

    id = Column(Integer, primary_key=True)
    ctx_id = Column(String, index=True)
    airline = Column(String, index=True)
    month = Column(String, index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    ctx_id = Column(String, index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Export(Base):
    __tablename__ = "exports"

    id = Column(Integer, primary_key=True)
    ctx_id = Column(String, index=True)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)
    ctx_id = Column(String, index=True, nullable=False)
    stage = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


# Helpful composite indices
Index("ix_bid_packages_ctx_airline", BidPackage.ctx_id, BidPackage.airline)
Index("ix_candidates_ctx_created", Candidate.ctx_id, Candidate.created_at)
Index("ix_exports_ctx_created", Export.ctx_id, Export.created_at)
