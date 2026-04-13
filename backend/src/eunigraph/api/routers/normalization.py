from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_db_session
from eunigraph.api.schemas.normalization import (
    NormalizationFindingResponse,
    NormalizationRunRequest,
    NormalizationRunResponse,
)
from eunigraph.modules.normalization.application import NormalizationService

router = APIRouter(prefix="/admin/normalization", tags=["admin", "normalization"])
DB_SESSION = Depends(get_db_session)
LIMIT_QUERY = Query(default=100, ge=1, le=500)


def _run_response(summary: object) -> NormalizationRunResponse:
    return NormalizationRunResponse.model_validate(summary)


def _finding_response(finding: object) -> NormalizationFindingResponse:
    return NormalizationFindingResponse.model_validate(finding)


@router.post("/run", response_model=NormalizationRunResponse)
def run_normalization(
    payload: NormalizationRunRequest,
    session: Session = DB_SESSION,
) -> NormalizationRunResponse:
    summary = NormalizationService(session).run(notes=payload.notes)
    return _run_response(summary)


@router.get("/status", response_model=NormalizationRunResponse | None)
def get_normalization_status(
    session: Session = DB_SESSION,
) -> NormalizationRunResponse | None:
    summary = NormalizationService(session).get_latest_summary()
    if summary is None:
        return None
    return _run_response(summary)


@router.get("/findings", response_model=list[NormalizationFindingResponse])
def list_normalization_findings(
    run_id: UUID | None = None,
    entity_type: str | None = None,
    confidence: str | None = None,
    auto_applied: bool | None = None,
    limit: int = LIMIT_QUERY,
    session: Session = DB_SESSION,
) -> list[NormalizationFindingResponse]:
    findings = NormalizationService(session).list_findings(
        run_id=run_id,
        entity_type=entity_type,
        confidence=confidence,
        auto_applied=auto_applied,
        limit=limit,
    )
    return [_finding_response(finding) for finding in findings]
