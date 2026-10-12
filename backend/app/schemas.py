from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "agent", "customer"]
Priority = Literal["low", "medium", "high"]
Status = Literal["open", "in_progress", "resolved", "closed"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterBusinessIn(BaseModel):
    business_name: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["agent", "customer"]


class BusinessOut(ORMModel):
    id: int
    name: str
    slug: str


class UserOut(ORMModel):
    id: int
    business_id: int
    name: str
    email: str
    role: Role
    created_at: datetime


class MeOut(UserOut):
    business: BusinessOut


class UserBrief(ORMModel):
    id: int
    name: str


class SenderOut(UserBrief):
    role: Role


class TicketCreateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    subject: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    priority: Priority
    message: str = Field(min_length=1, max_length=5000)


class TicketUpdateIn(BaseModel):
    status: Status | None = None
    assigned_agent_id: int | None = None


class TicketOut(ORMModel):
    id: int
    subject: str
    category: str
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    customer: UserBrief
    assigned_agent: UserBrief | None


class MessageOut(ORMModel):
    id: int
    ticket_id: int
    body: str
    has_attachment: bool
    created_at: datetime
    sender: SenderOut


class MessageIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    body: str = Field(min_length=1, max_length=5000)
