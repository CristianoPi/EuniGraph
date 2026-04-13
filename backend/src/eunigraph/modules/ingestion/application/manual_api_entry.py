from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from eunigraph.modules.ingestion.infrastructure.models import (
    DataSourceModel,
    IngestionRunModel,
    SourceRecordModel,
)

MANUAL_API_SOURCE_NAME = "Manual API Entry"
MANUAL_API_SOURCE_TYPE = "manual_api_entry"
MANUAL_API_TRIGGER = "manual-api"


def create_manual_source_record(
    session: Session,
    *,
    entity_type: str,
    source_identifier: str,
    action: str,
    payload: dict[str, Any],
    canonical_entity_id: UUID,
) -> SourceRecordModel:
    data_source = _get_or_create_manual_data_source(session)
    ingestion_run = IngestionRunModel(
        data_source_id=data_source.id,
        status="completed",
        completed_at=datetime.now(UTC),
        triggered_by=MANUAL_API_TRIGGER,
        raw_config={"action": action, "entity_type": entity_type},
        notes=f"Manual API {action} for {entity_type}",
    )
    session.add(ingestion_run)
    session.flush()

    raw_payload = {
        "action": action,
        "entity_type": entity_type,
        "canonical_entity_id": str(canonical_entity_id),
        "payload": payload,
    }
    checksum = hashlib.sha256(
        json.dumps(raw_payload, sort_keys=True).encode("utf-8"),
    ).hexdigest()
    source_record = SourceRecordModel(
        data_source_id=data_source.id,
        ingestion_run_id=ingestion_run.id,
        entity_type=entity_type,
        source_identifier=source_identifier,
        checksum=checksum,
        raw_payload=raw_payload,
    )
    session.add(source_record)
    session.flush()
    return source_record


def _get_or_create_manual_data_source(session: Session) -> DataSourceModel:
    data_source = session.query(DataSourceModel).filter_by(
        source_type=MANUAL_API_SOURCE_TYPE,
    ).one_or_none()
    if data_source is None:
        data_source = DataSourceModel(
            name=MANUAL_API_SOURCE_NAME,
            source_type=MANUAL_API_SOURCE_TYPE,
            description="Canonical entities created or updated manually through FastAPI.",
            is_active=True,
        )
        session.add(data_source)
        session.flush()
    return data_source
