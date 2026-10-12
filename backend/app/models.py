from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    business: Mapped[Business] = relationship(lazy="joined")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (Index("ix_tickets_business_id_status", "business_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped[User] = relationship(foreign_keys=[customer_id], lazy="joined")
    assigned_agent: Mapped[User | None] = relationship(foreign_keys=[assigned_agent_id], lazy="joined")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_ticket_id_created_at", "ticket_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text, default="")
    attachment_path: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sender: Mapped[User] = relationship(lazy="joined")

    @property
    def has_attachment(self) -> bool:
        return self.attachment_path is not None
