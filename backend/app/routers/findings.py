from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import ExplainResponse
from app.services.rag.explain_service import ExplainService
from app.services.rag.llms import get_llm
from app.services.rag.retriever import ChromaRetriever, StaticRetriever
from app.services.scan_service import ScanService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/findings", tags=["findings"])


def get_explain_service() -> ExplainService:
    retriever: StaticRetriever | ChromaRetriever = StaticRetriever()
    if settings.rag_enabled:
        try:
            retriever = ChromaRetriever()
        except Exception as extra:
            logger.warning("Using empty retriever; Chroma index unavailable (%s)", extra)
            retriever = StaticRetriever()
    return ExplainService(retriever, llm=get_llm(), k=settings.rag_k)


@router.post("/{finding_id}/explain", response_model=ExplainResponse)
def explain_finding(
    finding_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[ExplainService, Depends(get_explain_service)],
) -> ExplainResponse:
    finding = ScanService(db).get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    result = service.explain(finding)
    return ExplainResponse(
        finding_id=finding.id,
        explanation=result.explanation,
        fix=result.fix,
        language=result.language,
        confidence=result.confidence,
        model=result.model,
        retrieved_doc_ids=result.retrieved_doc_ids,
    )
