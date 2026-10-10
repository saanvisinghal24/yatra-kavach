"""Immutable publication content; withdrawal preserves the operational audit trail."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class Advisory(Base):
    __tablename__ = 'advisory'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey('route.id', ondelete='CASCADE'), index=True)
    checkpoint_id: Mapped[int | None] = mapped_column(ForeignKey('checkpoint.id', ondelete='CASCADE'))
    author_id: Mapped[int | None] = mapped_column(ForeignKey('user.id', ondelete='SET NULL'))
    kind: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(160))
    title_hi: Mapped[str] = mapped_column(String(160), default='')
    body: Mapped[str] = mapped_column(Text)
    body_hi: Mapped[str] = mapped_column(Text, default='')
    source_url: Mapped[str | None] = mapped_column(String(2000))
    checkpoint_status: Mapped[str | None] = mapped_column(String(16))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_by: Mapped[int | None] = mapped_column(ForeignKey('user.id', ondelete='SET NULL'))
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
