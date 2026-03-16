"""Pydantic models for Fabric API responses."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class _FabricModel(BaseModel):
    """Base model with camelCase alias support and extra field passthrough."""

    model_config = ConfigDict(
        extra="allow",
        alias_generator=to_camel,
        populate_by_name=True,
    )


class Tag(_FabricModel):
    id: str | None = None
    name: str | None = None
    description: str | None = None


class Resource(_FabricModel):
    id: str
    kind: str
    name: str | None = None
    description: str | None = None
    parent_id: str | None = None
    root_id: str | None = None
    url: str | None = None
    mime_type: str | None = None
    extension: str | None = None
    file_url: str | None = None
    created_at: str | None = None
    modified_at: str | None = None
    tags: list[Tag] = []


class SearchHit(Resource):
    score: float | None = None


class ResourceRoot(_FabricModel):
    id: str
    type: str
    subtype: str | None = None
    is_private: bool = False
    created_at: str | None = None
    modified_at: str | None = None
    folder: dict | None = None

    @property
    def folder_name(self) -> str | None:
        if self.folder and isinstance(self.folder, dict):
            return self.folder.get("name")
        return None


class PaginatedResponse(_FabricModel, Generic[T]):
    total: int | None = None
    has_more: bool = False
    next_cursor: str | None = None
    items: list[T] = []


class PresignedUpload(_FabricModel):
    url: str
    headers: dict[str, str | None] = {}
