from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class MerchantCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None


class MerchantLogin(BaseModel):
    email: EmailStr
    password: str


class MerchantResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    razorpay_key_id: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    email: str | None = None
