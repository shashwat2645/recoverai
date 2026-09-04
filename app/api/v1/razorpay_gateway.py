from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.schemas.razorpay_gateway import PaymentLinkRequest, PaymentLinkResponse
from app.services.razorpay_service import RazorpayService

router = APIRouter(tags=["Razorpay Integration"])


@router.post("/payment-link", response_model=PaymentLinkResponse, status_code=status.HTTP_201_CREATED, summary="Generate Razorpay Payment Link")
def create_payment_link_endpoint(
    request_in: PaymentLinkRequest,
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Generates a Razorpay Payment Link using the merchant's gateway credentials or global test configuration.
    """
    raw_res = RazorpayService.create_payment_link(
        amount=request_in.amount,
        currency=request_in.currency,
        description=request_in.description,
        customer_name=request_in.customer_name,
        customer_email=request_in.customer_email,
        customer_phone=request_in.customer_phone,
        reference_id=request_in.reference_id,
        key_id=current_merchant.razorpay_key_id,
        key_secret=current_merchant.razorpay_key_secret
    )

    amount_in_rupees = raw_res.get("amount", 0) / 100.0 if raw_res.get("amount") else request_in.amount

    link_id = raw_res.get("id", "plink_unknown")
    fallback_url = f"https://rzp.io/i/{link_id[:10]}" if link_id != "plink_unknown" else "https://rzp.io/l/payment"
    return PaymentLinkResponse(
        payment_link_id=link_id,
        short_url=raw_res.get("short_url", fallback_url),
        status=raw_res.get("status", "created"),
        amount=amount_in_rupees,
        currency=raw_res.get("currency", request_in.currency),
        reference_id=raw_res.get("reference_id")
    )
