"""Fabric API client — single entry point for all operations."""

from __future__ import annotations

import os
from typing import Any

from fabric_client.exceptions import FabricError
from fabric_client.http import FabricHTTP
from fabric_client.models import (
    PaginatedResponse,
    PresignedUpload,
    Resource,
    ResourceRoot,
    SearchHit,
    Tag,
)


class FabricClient:
    """Async client for the Fabric v2 REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        workspace_id: str | None = None,
    ):
        resolved_key = api_key or os.environ.get("FABRIC_API_KEY")
        if not resolved_key:
            raise FabricError(
                "API key required. Pass api_key= or set FABRIC_API_KEY env var."
            )
        resolved_url = base_url or os.environ.get(
            "FABRIC_BASE_URL", "https://api.fabric.so/v2"
        )
        self._http = FabricHTTP(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=timeout,
            max_retries=max_retries,
            workspace_id=workspace_id,
        )

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self) -> FabricClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # --- Resource Roots ---

    async def list_roots(self) -> list[ResourceRoot]:
        data = await self._http.get("/resource-roots")
        roots = data.get("data", {}).get("roots", [])
        return [ResourceRoot.model_validate(item) for item in roots]

    async def get_root(self, root_id: str) -> ResourceRoot:
        data = await self._http.get(f"/resource-roots/{root_id}")
        return ResourceRoot.model_validate(data)

    # --- Resources ---

    async def get_resource(self, resource_id: str) -> Resource:
        data = await self._http.get(f"/resources/{resource_id}")
        return Resource.model_validate(data)

    async def filter_resources(
        self,
        kind: list[str] | None = None,
        parent_id: str | None = None,
        root_id: str | None = None,
        tag_ids: list[str] | None = None,
        name: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        order_by: str | None = None,
        order_direction: str = "DESC",
    ) -> PaginatedResponse[Resource]:
        body: dict[str, Any] = {"limit": limit}
        if kind:
            body["kind"] = kind
        if parent_id:
            body["parentId"] = parent_id
        if root_id:
            body["rootId"] = root_id
        if tag_ids:
            body["tagIds"] = tag_ids
        if name:
            body["name"] = name
        if cursor:
            body["cursor"] = cursor
        if order_by:
            body["order"] = {"property": order_by, "direction": order_direction}

        data = await self._http.post("/resources/filter", json=body)
        return PaginatedResponse[Resource].model_validate(
            {
                "total": data.get("total"),
                "hasMore": data.get("hasMore", False),
                "nextCursor": data.get("nextCursor"),
                "items": data.get("resources", []),
            }
        )

    async def delete_resources(
        self, resource_ids: list[str], archive: bool = False
    ) -> None:
        await self._http.post(
            "/resources/delete",
            json={"resourceIds": resource_ids, "archive": archive},
        )

    async def recover_resources(self, resource_ids: list[str]) -> None:
        await self._http.post("/resources/recover", json={"resourceIds": resource_ids})

    # --- Search ---

    async def search(
        self,
        text: str,
        kinds: list[str] | None = None,
        tag_ids: list[str] | None = None,
        root_ids: list[str] | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> PaginatedResponse[SearchHit]:
        body: dict[str, Any] = {
            "mode": "hybrid",
            "text": text,
            "pagination": {"page": page, "pageSize": limit},
        }
        filters: dict[str, Any] = {}
        if kinds:
            filters["kinds"] = kinds
        if tag_ids:
            filters["tagIds"] = tag_ids
        if root_ids:
            filters["rootIds"] = root_ids
        if filters:
            body["filters"] = filters

        data = await self._http.post("/search", json=body)
        return PaginatedResponse[SearchHit].model_validate(
            {
                "total": data.get("total"),
                "hasMore": data.get("hasMore", False),
                "items": data.get("hits", []),
            }
        )

    # --- Bookmarks ---

    async def create_bookmark(
        self,
        url: str,
        parent_id: str,
        name: str | None = None,
        tags: list[dict[str, str]] | None = None,
        comment: str | None = None,
    ) -> Resource:
        body: dict[str, Any] = {"url": url, "parentId": parent_id}
        if name:
            body["name"] = name
        if tags:
            body["tags"] = tags
        if comment:
            body["comment"] = {"content": comment}
        data = await self._http.post("/bookmarks", json=body)
        return Resource.model_validate(data)

    # --- Notepads ---

    async def create_notepad(
        self,
        parent_id: str,
        name: str | None = None,
        text: str | None = None,
        tags: list[dict[str, str]] | None = None,
        comment: str | None = None,
    ) -> Resource:
        body: dict[str, Any] = {"parentId": parent_id}
        if name:
            body["name"] = name
        if text is not None:
            body["text"] = text
        if tags:
            body["tags"] = tags
        if comment:
            body["comment"] = {"content": comment}
        data = await self._http.post("/notepads", json=body)
        return Resource.model_validate(data)

    async def get_notepad_content(self, resource_id: str) -> str:
        return await self._http.get_text(f"/notepads/{resource_id}/content")

    # --- Folders ---

    async def create_folder(
        self,
        parent_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Resource:
        body: dict[str, Any] = {"parentId": parent_id}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        data = await self._http.post("/folders", json=body)
        return Resource.model_validate(data)

    # --- Tags ---

    async def list_tags(self, limit: int = 100, name: str | None = None) -> list[Tag]:
        params: dict[str, Any] = {"limit": limit}
        if name:
            params["name"] = name
        data = await self._http.get("/tags", params=params)
        items = data.get("data", {}).get("tags", [])
        return [Tag.model_validate(item) for item in items]

    # --- Files ---

    async def get_upload_url(
        self, filename: str, size: int, resource_id: str | None = None
    ) -> PresignedUpload:
        params: dict[str, Any] = {"filename": filename, "size": size}
        if resource_id:
            params["resourceId"] = resource_id
        data = await self._http.get("/upload", params=params)
        return PresignedUpload.model_validate(data)

    async def upload_file_data(
        self, url: str, data: bytes, headers: dict[str, str] | None = None
    ) -> None:
        await self._http.put_binary(url, data=data, headers=headers)

    async def create_file(
        self,
        attachment_path: str,
        attachment_filename: str,
        parent_id: str,
        mime_type: str,
        name: str | None = None,
        tags: list[dict[str, str]] | None = None,
        comment: str | None = None,
    ) -> Resource:
        body: dict[str, Any] = {
            "attachment": {"path": attachment_path, "filename": attachment_filename},
            "parentId": parent_id,
            "mimeType": mime_type,
        }
        if name:
            body["name"] = name
        if tags:
            body["tags"] = tags
        if comment:
            body["comment"] = {"content": comment}
        data = await self._http.post("/files", json=body)
        return Resource.model_validate(data)
