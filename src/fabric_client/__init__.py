"""Fabric client library — async and sync clients for the Fabric v2 REST API."""

from fabric_client._compat import FabricSyncClient
from fabric_client.client import FabricClient
from fabric_client.exceptions import (
    AuthenticationError,
    FabricAPIError,
    FabricError,
    NotFoundError,
    RateLimitError,
)
from fabric_client.models import (
    PaginatedResponse,
    PresignedUpload,
    Resource,
    ResourceRoot,
    SearchHit,
    Tag,
)

__all__ = [
    "FabricClient",
    "FabricSyncClient",
    "FabricError",
    "FabricAPIError",
    "NotFoundError",
    "RateLimitError",
    "AuthenticationError",
    "Resource",
    "ResourceRoot",
    "SearchHit",
    "PaginatedResponse",
    "PresignedUpload",
    "Tag",
]
