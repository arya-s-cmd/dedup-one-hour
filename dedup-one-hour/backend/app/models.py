from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, ForeignKey, Index
from .db import Base

class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str | None] = mapped_column(String(256))
    phone: Mapped[str | None] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(256), index=True)
    timestamp: Mapped[str | None] = mapped_column(String(32), index=True)  # ISO string
    text: Mapped[str | None] = mapped_column(Text)
    canonical_of: Mapped[int | None] = mapped_column(Integer, index=True)

class DuplicateGroup(Base):
    __tablename__ = "dup_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24), default="suggested")
    score_summary: Mapped[str | None] = mapped_column(Text)

class GroupMember(Base):
    __tablename__ = "group_members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("dup_groups.id", ondelete="CASCADE"))
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"))

class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("dup_groups.id", ondelete="CASCADE"))
    actor: Mapped[str] = mapped_column(String(128))
    decision: Mapped[str] = mapped_column(String(24))
    target_canonical_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str | None] = mapped_column(String(32))

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(64))
    before_json: Mapped[str | None] = mapped_column(Text)
    after_json: Mapped[str | None] = mapped_column(Text)
    prev_hash: Mapped[str | None] = mapped_column(String(128))
    hash: Mapped[str] = mapped_column(String(128))
Index("ix_complaints_timestamp_day", Complaint.timestamp)
