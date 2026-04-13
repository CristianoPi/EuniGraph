from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_db_session
from eunigraph.api.schemas.source_records import SourceRecordResponse
from eunigraph.modules.ingestion.infrastructure.models import (
    DataSourceModel,
    SourceRecordModel,
)

router = APIRouter(prefix="/source-records", tags=["source-records"])
DB_SESSION = Depends(get_db_session)
LIMIT_QUERY = Query(default=50, le=500)
OFFSET_QUERY = Query(default=0, ge=0)


def _source_record_response(record: object) -> SourceRecordResponse:
    return SourceRecordResponse.model_validate(record)


@router.get("", response_model=list[SourceRecordResponse])
def get_source_records(
    entity_type: str | None = None,
    source_identifier: str | None = None,
    source_type: str | None = None,
    canonical_entity_id: UUID | None = None,
    data_source_id: UUID | None = None,
    ingestion_run_id: UUID | None = None,
    limit: int = LIMIT_QUERY,
    offset: int = OFFSET_QUERY,
    session: Session = DB_SESSION,
) -> list[SourceRecordResponse]:
    query = select(SourceRecordModel).order_by(SourceRecordModel.ingested_at.desc())
    if entity_type:
        query = query.where(SourceRecordModel.entity_type == entity_type)
    if source_identifier:
        query = query.where(SourceRecordModel.source_identifier == source_identifier)
    if source_type:
        query = query.join(
            DataSourceModel,
            SourceRecordModel.data_source_id == DataSourceModel.id,
        ).where(DataSourceModel.source_type == source_type)
    if canonical_entity_id:
        query = query.where(
            SourceRecordModel.raw_payload["canonical_entity_id"].astext
            == str(canonical_entity_id),
        )
    if data_source_id:
        query = query.where(SourceRecordModel.data_source_id == data_source_id)
    if ingestion_run_id:
        query = query.where(SourceRecordModel.ingestion_run_id == ingestion_run_id)
    records = list(session.scalars(query.limit(limit).offset(offset)))
    return [_source_record_response(record) for record in records]


@router.get("/{source_record_id}", response_model=SourceRecordResponse)
def get_source_record(
    source_record_id: UUID,
    session: Session = DB_SESSION,
) -> SourceRecordResponse:
    record = session.get(SourceRecordModel, source_record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source record not found")
    return _source_record_response(record)
