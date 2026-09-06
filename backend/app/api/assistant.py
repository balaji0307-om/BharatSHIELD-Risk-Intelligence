"""
AI Risk Assistant API: Constrained, defense-oriented analysis layer.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.services.assistant_service import RiskAssistantService

router = APIRouter(prefix="/assistant", tags=["AI Risk Assistant"])

class AssistantQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language question regarding risk telemetry")

class AssistantQueryResponse(BaseModel):
    response: str
    guardrail_status: str
    grounded_data: dict | None = None

@router.post("/ask", response_model=AssistantQueryResponse, summary="Inquire with AI Risk Assistant")
def ask_assistant(
    payload: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    result = RiskAssistantService.answer_query(db, payload.query, merchant_id=current_merchant)
    return result
