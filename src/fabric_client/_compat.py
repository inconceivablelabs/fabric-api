"""Synchronous wrapper around FabricClient for non-async consumers."""

from __future__ import annotations

import asyncio
from typing import Any

from fabric_client.client import FabricClient
from fabric_client.models import (
    PaginatedResponse,
    PresignedUpload,
    Resource,
    ResourceRoot,
    SearchHit,
    Tag,
)


class FabricSyncClient:
    """Sync wrapper around FabricClient.

    Uses a persistent event loop so the httpx connection pool stays alive
    across calls. Suitable for scripts, notebooks, and subprocess calls
    from n8n.
    """

    def __init__(self, **kwargs: Any):
        self._client = FabricClient(**kwargs)
        self._loop = asyncio.new_event_loop()

    def _run(self, coro: Any) -> Any:
        return self._loop.run_until_complete(coro)

    def close(self) -> None:
        self._run(self._client.close())
        self._loop.close()

    # --- Resource Roots ---

    def list_roots(self) -> list[ResourceRoot]:
        return self._run(self._client.list_roots())

    def get_root(self, root_id: str) -> ResourceRoot:
        return self._run(self._client.get_root(root_id))

    # --- Resources ---

    def get_resource(self, resource_id: str) -> Resource:
        return self._run(self._client.get_resource(resource_id))

    def filter_resources(self, **kwargs: Any) -> PaginatedResponse[Resource]:
        return self._run(self._client.filter_resources(**kwargs))

    def delete_resources(self, resource_ids: list[str], archive: bool = False) -> None:
        self._run(self._client.delete_resources(resource_ids, archive=archive))

    def recover_resources(self, resource_ids: list[str]) -> None:
        self._run(self._client.recover_resources(resource_ids))

    # --- Search ---

    def search(self, text: str, **kwargs: Any) -> PaginatedResponse[SearchHit]:
        return self._run(self._client.search(text, **kwargs))

    # --- Bookmarks ---

    def create_bookmark(self, **kwargs: Any) -> Resource:
        return self._run(self._client.create_bookmark(**kwargs))

    # --- Notepads ---

    def create_notepad(self, **kwargs: Any) -> Resource:
        return self._run(self._client.create_notepad(**kwargs))

    def get_notepad_content(self, resource_id: str) -> str:
        return self._run(self._client.get_notepad_content(resource_id))

    # --- Folders ---

    def create_folder(self, **kwargs: Any) -> Resource:
        return self._run(self._client.create_folder(**kwargs))

    # --- Tags ---

    def list_tags(self, **kwargs: Any) -> list[Tag]:
        return self._run(self._client.list_tags(**kwargs))

    # --- Files ---

    def get_upload_url(self, **kwargs: Any) -> PresignedUpload:
        return self._run(self._client.get_upload_url(**kwargs))

    def upload_file_data(self, url: str, data: bytes, **kwargs: Any) -> None:
        self._run(self._client.upload_file_data(url, data, **kwargs))

    def create_file(self, **kwargs: Any) -> Resource:
        return self._run(self._client.create_file(**kwargs))
