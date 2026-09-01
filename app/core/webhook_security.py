import hmac
import hashlib


def verify_razorpay_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature sent by Razorpay in the X-Razorpay-Signature header.
    Uses hmac.compare_digest to prevent timing attack vulnerabilities.
    """
    if not secret or not signature:
        return False
    try:
        generated_signature = hmac.new(
            secret.encode('utf-8'),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(generated_signature, signature)
    except Exception:
        return False
