from typing import Literal
from uuid import UUID

from ninja import Schema
from pydantic import EmailStr, field_validator


class RegisterSchema(Schema):
    full_name: str
    email: EmailStr
    phone_number: str
    password: str
    verification_channel: Literal["email", "phone"] = "email"


class LoginSchema(Schema):
    username: str
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return str(value).strip()


class VerifyOtpSchema(Schema):
    identifier: str
    verification_channel: Literal["email", "phone"]
    code: str

    @field_validator("identifier", "code", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return str(value).strip()


class ResendOtpSchema(Schema):
    identifier: str
    verification_channel: Literal["email", "phone"]

    @field_validator("identifier", mode="before")
    @classmethod
    def normalize_identifier(cls, value):
        return str(value).strip()


class UserResponseSchema(Schema):
    id: UUID
    full_name: str
    email: EmailStr
    avatar: str | None
    is_email_verified: bool
    is_phone_verified: bool


class MessageSchema(Schema):
    success: bool
    message: str


class OtpSentSchema(MessageSchema):
    verification_channel: str


class TokenSchema(Schema):
    access: str
    refresh: str


class AuthResponseSchema(Schema):
    user: UserResponseSchema
    tokens: TokenSchema
