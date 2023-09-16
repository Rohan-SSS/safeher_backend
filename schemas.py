from datetime import datetime
from pydantic import BaseModel
from typing import List


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
    is_anonymous: bool


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    ticket_id: int
    teacher_id: int
    is_open: bool
    report_content: str
    lat: float
    long: float

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


class SOSRequest(BaseModel):
    user_id: int
    lat: float
    long: float


class ChatbotRequest(BaseModel):
    message: str


class ChatbotResponse(BaseModel):
    response: str


class Center(BaseModel):
    latitude: float
    longitude: float


class Area(BaseModel):
    center: Center
    radius: int


class Markers(BaseModel):
    markers: List[Area]


class UserSchema(BaseModel):
    user_id: str
    name: str


class ChatMessageSchema(BaseModel):
    user: UserSchema
    message_text: str
    created_at: str

    class Config:
        from_attributes = True
