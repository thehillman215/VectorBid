from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid

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


# New models for PostgreSQL schema and trip sheet handling

class User(Base):
    """User accounts for authentication"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default='pilot')
    status = Column(String(20), nullable=False, default='active')
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PilotContract(Base):
    """Uploaded pilot contracts (trip sheets)"""
    __tablename__ = "pilot_contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airline = Column(String(10), nullable=False, index=True)
    contract_version = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_content = Column(LargeBinary, nullable=False)  # Store PDF content
    mime_type = Column(String(100), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    status = Column(String(20), nullable=False, default='uploaded')
    parsing_status = Column(String(20), nullable=False, default='pending')
    parsed_data = Column(JSON)  # Extracted trip data
    error_message = Column(Text)
    approved_at = Column(DateTime)
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ContractRule(Base):
    """Individual rules extracted from contracts"""
    __tablename__ = "contract_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('pilot_contracts.id', ondelete='CASCADE'), nullable=False)
    rule_id = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100))
    description = Column(Text, nullable=False)
    rule_text = Column(Text, nullable=False)
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Helpful composite indices
Index("ix_bid_packages_ctx_airline", BidPackage.ctx_id, BidPackage.airline)
Index("ix_candidates_ctx_created", Candidate.ctx_id, Candidate.created_at)
Index("ix_exports_ctx_created", Export.ctx_id, Export.created_at)

# New indices for PostgreSQL models
Index("ix_pilot_contracts_airline_status", PilotContract.airline, PilotContract.status)
Index("ix_contract_rules_contract_category", ContractRule.contract_id, ContractRule.category)
