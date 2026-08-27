"""Contratos compartidos de la API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExplanationOut(ApiModel):
    """El bloque "¿por qué esto?" (A21).

    Es parte del contrato de toda recomendación, no un extra opcional. Las dos
    confianzas van separadas a propósito y nunca se promedian.
    """

    summary_key: str
    inputs_used: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    evidence_level: str
    evidence_confidence: float = Field(ge=0.0, le=1.0)
    personal_confidence: float = Field(ge=0.0, le=1.0)
    sample_size: int = Field(ge=0)
    uncertainty_keys: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)


class ErrorOut(ApiModel):
    code: str
    message_key: str
    details: dict[str, Any] = Field(default_factory=dict)


class MeasuredOut(ApiModel):
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    observed_at: str | None = None
    notes: str | None = None
