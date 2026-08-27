from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate
from app.core.security import get_password_hash, verify_password


def get_merchant_by_email(db: Session, email: str) -> Merchant | None:
    """
    Fetch a merchant record by email address.
    """
    stmt = select(Merchant).where(Merchant.email == email)
    return db.execute(stmt).scalar_one_or_none()


def get_merchant_by_id(db: Session, merchant_id: str) -> Merchant | None:
    """
    Fetch a merchant record by primary key ID.
    """
    stmt = select(Merchant).where(Merchant.id == merchant_id)
    return db.execute(stmt).scalar_one_or_none()


def create_merchant(db: Session, merchant_in: MerchantCreate) -> Merchant:
    """
    Create a new merchant account with hashed password storage.
    """
    db_merchant = Merchant(
        name=merchant_in.name,
        email=merchant_in.email,
        hashed_password=get_password_hash(merchant_in.password),
        razorpay_key_id=merchant_in.razorpay_key_id,
        razorpay_key_secret=merchant_in.razorpay_key_secret
    )
    db.add(db_merchant)
    db.commit()
    db.refresh(db_merchant)
    return db_merchant


def authenticate_merchant(db: Session, email: str, password: str) -> Merchant | None:
    """
    Authenticate a merchant by verifying credentials.
    """
    merchant = get_merchant_by_email(db, email)
    if not merchant:
        return None
    if not verify_password(password, merchant.hashed_password):
        return None
    return merchant
