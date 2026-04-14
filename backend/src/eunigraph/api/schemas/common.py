from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    detail: str


class ValidationErrorItemResponse(BaseModel):
    type: str
    loc: list[Any]
    msg: str
    input: Any | None = None


class ValidationErrorResponse(BaseModel):
    detail: list[ValidationErrorItemResponse]
