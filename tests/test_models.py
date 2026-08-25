from sqlalchemy.orm import Session
from app.models import Merchant, PaymentEvent, RecoveryCase, RecoveryStatus, AuditLog, PolicyDocument


def test_create_merchant_and_relationships(db_session: Session):
    # 1. Create Merchant
    merchant = Merchant(
        name="Test Merchant Corp",
        email="support@testmerchant.com",
        hashed_password="secure_hashed_password_sample",
        razorpay_key_id="rzp_test_12345",
        razorpay_key_secret="secret_12345"
    )
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)

    assert merchant.id is not None
    assert merchant.email == "support@testmerchant.com"

    # 2. Add Payment Event
    event = PaymentEvent(
        merchant_id=merchant.id,
        event_id="evt_test_payment_failed_001",
        event_type="payment.failed",
        amount=1499.00,
        currency="INR",
        customer_email="customer@example.com",
        customer_phone="+919876543210",
        failure_reason="BAD_REQUEST_PAYMENT_TIMED_OUT",
        raw_payload={"event": "payment.failed", "id": "evt_test_payment_failed_001"}
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.merchant_id == merchant.id

    # 3. Create Recovery Case
    case = RecoveryCase(
        merchant_id=merchant.id,
        payment_event_id=event.id,
        status=RecoveryStatus.DETECTED.value,
        risk_score=0.85,
        amount_at_risk=1499.00,
        customer_name="John Doe",
        customer_email="customer@example.com"
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    assert case.id is not None
    assert case.status == "DETECTED"

    # 4. Create Audit Log
    audit = AuditLog(
        recovery_case_id=case.id,
        merchant_id=merchant.id,
        event_type="RISK_ANALYSIS",
        prompt_context={"failure_reason": event.failure_reason},
        ai_reasoning="Payment timed out due to bank network latency.",
        confidence_score=0.92,
        recommended_action="GENERATE_PAYMENT_LINK",
        executed_action="GENERATE_PAYMENT_LINK",
        execution_status="SUCCESS"
    )
    db_session.add(audit)

    # 5. Create Policy Document
    policy = PolicyDocument(
        merchant_id=merchant.id,
        title="Retry & Payment Link Terms",
        policy_type="RETRY",
        content="Max 3 retries within 72 hours. Send SMS reminder after 24h."
    )
    db_session.add(policy)

    db_session.commit()

    # Verify relationships
    db_session.refresh(merchant)
    assert len(merchant.payment_events) == 1
    assert len(merchant.recovery_cases) == 1
    assert len(merchant.policy_documents) == 1
    assert len(case.audit_logs) == 1
