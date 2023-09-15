from sqlalchemy import (
    TIMESTAMP,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    BOOLEAN,
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(Text, nullable=False)
    is_teacher = Column(BOOLEAN, default=False, nullable=False)
    phone_number = Column(String, nullable=False)

    community_messages = relationship(
        "CommunityChatMessage",
        backref="user",
        foreign_keys="[CommunityChatMessage.user_id]",
    )
    tickets = relationship("Ticket", backref="user", foreign_keys="[Ticket.user_id]")
    ticket_chat_messages = relationship(
        "TicketChatMessage",
        foreign_keys="[TicketChatMessage.user_id]",
        backref="user",
    )


class CommunityChatMessage(Base):
    __tablename__ = "community_chat_messages"

    message_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    message_text = Column(Text, nullable=False)
    created_at = Column("created_at", TIMESTAMP, server_default=func.now())


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    is_open = Column(BOOLEAN, default=True, nullable=False)
    is_anonymous = Column(BOOLEAN, default=False, nullable=False)
    ticket_chat_messages = relationship("TicketChatMessage", backref="ticket")

    reports = relationship(
        "TicketReport", backref="ticket", foreign_keys="[TicketReport.ticket_id]"
    )


class TicketReport(Base):
    __tablename__ = "ticket_reports"

    report_id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=False)
    report_content = Column(Text, nullable=False)
    lat = Column(Float(precision=53), nullable=False)
    long = Column(Float(precision=53), nullable=False)


class TicketChatMessage(Base):
    __tablename__ = "ticket_chat_messages"

    message_id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    message_text = Column(Text, nullable=False)
    created_at = Column("created_at", TIMESTAMP, server_default=func.now())
