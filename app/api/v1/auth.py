from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.merchant import MerchantCreate, MerchantLogin, MerchantResponse, Token
from app.services.merchant_service import (
    get_merchant_by_email,
    create_merchant,
    authenticate_merchant,
)
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(tags=["Merchant Auth"])


@router.post("/register", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED, summary="Register Merchant Account")
def register_merchant(
    merchant_in: MerchantCreate,
    db: Session = Depends(get_db)
):
    """
    Registers a new merchant with a unique email address.
    """
    existing_merchant = get_merchant_by_email(db, merchant_in.email)
    if existing_merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A merchant with this email address already exists."
        )

    merchant = create_merchant(db, merchant_in)
    return merchant


@router.post("/login", response_model=Token, summary="Authenticate Merchant & Issue JWT")
def login_merchant(
    credentials: MerchantLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticates a merchant and returns a signed JWT Bearer Token.
    """
    merchant = authenticate_merchant(db, credentials.email, credentials.password)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": merchant.id, "email": merchant.email}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=MerchantResponse, summary="Get Current Merchant Profile")
def get_current_merchant_profile(
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Retrieves the authenticated merchant's profile. Requires JWT Bearer Authorization header.
    """
    return current_merchant
