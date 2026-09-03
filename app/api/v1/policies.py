from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.models.policy_document import PolicyDocument
from app.schemas.policy import PolicyCreate, PolicyResponse, PolicyListResponse
from app.services.rag_service import RAGService

router = APIRouter(tags=["Merchant Policies"])


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED, summary="Add & Vector Index Merchant Policy")
def create_policy_document(
    policy_in: PolicyCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Creates and vector-indexes a new merchant policy document for AI RAG retrieval.
    """
    policy = RAGService.index_policy_document(
        db=db,
        merchant_id=current_merchant.id,
        title=policy_in.title,
        policy_type=policy_in.policy_type,
        content=policy_in.content
    )
    return policy


@router.get("", response_model=PolicyListResponse, summary="List Merchant Policy Documents")
def list_policy_documents(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Lists all policy documents belonging to the authenticated merchant.
    """
    stmt = select(PolicyDocument).where(
        PolicyDocument.merchant_id == current_merchant.id,
        PolicyDocument.is_active == True
    ).order_by(PolicyDocument.created_at.desc())

    policies = db.execute(stmt).scalars().all()
    return PolicyListResponse(total=len(policies), policies=policies)
