from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.merchant import Merchant
from app.services.merchant_service import get_merchant_by_id

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_current_merchant(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Merchant:
    """
    FastAPI Dependency to extract and validate the JWT Bearer token, returning the current Merchant.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    merchant_id: str | None = payload.get("sub")
    if merchant_id is None:
        raise credentials_exception

    merchant = get_merchant_by_id(db, merchant_id)
    if merchant is None:
        raise credentials_exception

    if not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant account is inactive"
        )

    return merchant
