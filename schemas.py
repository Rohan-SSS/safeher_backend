from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    name: str
    phone_number: str


class UserLogin(UserBase):
    password: str


class User(UserBase):
    user_id: int
    name: str
    phone_number: str
    is_teacher: bool

    class Config:
        from_attributes = True


# Ticket
class TicketBase(BaseModel):
    user_id: int


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    ticket_id: int
    teacher_id: int
    is_open: bool

    class Config:
        from_attributes = True


# TicketChatMessage
class TickerChatMessageBase(BaseModel):
    message_text: str
    user_id: int


class TicketChatMessageCreate(TickerChatMessageBase):
    ticket_id: int


class TicketChatMessage(TickerChatMessageBase):
    message_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommunityChatMessageBase(BaseModel):
    message_text: str
    user_id: int


class CommunityChatMessageCreate(CommunityChatMessageBase):
    pass


class CommunityChatMessage(CommunityChatMessageBase):
    message_id: int
    created_at: datetime

    class Config:
        from_attributes = True
