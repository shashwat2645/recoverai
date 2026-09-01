from pydantic import BaseModel, EmailStr


class PaymentLinkRequest(BaseModel):
    amount: float = 1499.00
    currency: str = "INR"
    description: str = "RecoverAI Revenue Recovery Link"
    customer_name: str | None = "Jane Doe"
    customer_email: EmailStr = "customer@example.com"
    customer_phone: str | None = "+919876543210"
    reference_id: str | None = None


class PaymentLinkResponse(BaseModel):
    payment_link_id: str
    short_url: str
    status: str
    amount: float
    currency: str
    reference_id: str | None = None
