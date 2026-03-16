"""Fabric MCP server definition."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from fabric_client import FabricClient
from fabric_client.exceptions import (
    AuthenticationError,
    FabricAPIError,
    NotFoundError,
    RateLimitError,
)


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manage FabricClient lifecycle."""
    async with FabricClient() as client:
        yield {"client": client}


mcp = FastMCP("Fabric", lifespan=_lifespan)


def _format_api_error(e: FabricAPIError) -> str:
    """Format a Fabric API error as a user-friendly message."""
    if isinstance(e, NotFoundError):
        return f"Not found: {e.detail}"
    if isinstance(e, AuthenticationError):
        return f"Authentication failed: {e.detail}. Check FABRIC_API_KEY."
    if isinstance(e, RateLimitError):
        retry = f" Retry after {e.retry_after}s." if e.retry_after else ""
        return f"Rate limited by Fabric API.{retry}"
    return f"Fabric API error (HTTP {e.status_code}): {e.detail}"


@mcp.tool()
async def search(
    query: str,
    ctx: Context,
    kinds: list[str] | None = None,
    tag_ids: list[str] | None = None,
    root_ids: list[str] | None = None,
    limit: int = 20,
) -> str:
    """Search Fabric content using hybrid semantic + keyword search.

    Args:
        query: Search text
        kinds: Filter by resource kinds (notepad, bookmark, document, etc.)
        tag_ids: Filter by tag IDs
        root_ids: Filter by root IDs (spaces)
        limit: Max results (default 20)
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        results = await client.search(
            text=query,
            kinds=kinds,
            tag_ids=tag_ids,
            root_ids=root_ids,
            limit=limit,
        )
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    if not results.items:
        return "No results found."

    lines = [f"Found {results.total or len(results.items)} results:\n"]
    for hit in results.items:
        score = f" (score: {hit.score:.2f})" if hit.score else ""
        name = hit.name or "(untitled)"
        lines.append(f"- **{name}** [{hit.kind}] id={hit.id}{score}")
        if hit.url:
            lines.append(f"  URL: {hit.url}")
    return "\n".join(lines)


# --- Resource Browsing Tools ---


@mcp.tool()
async def list_roots(ctx: Context) -> str:
    """List all Fabric root containers (inbox, spaces, integrations).

    Returns top-level organizational containers. Use root IDs to
    filter resources or as parent_id when creating content.
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        roots = await client.list_roots()
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    if not roots:
        return "No roots found."
    lines = ["Fabric roots:\n"]
    for root in roots:
        name = root.folder_name or "(unnamed)"
        subtype = f" ({root.subtype})" if root.subtype else ""
        lines.append(f"- **{name}** [{root.type}{subtype}] id={root.id}")
    return "\n".join(lines)


@mcp.tool()
async def get_resource(resource_id: str, ctx: Context) -> str:
    """Get detailed information about a specific Fabric resource.

    Args:
        resource_id: The resource UUID
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        resource = await client.get_resource(resource_id)
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    lines = [
        f"**{resource.name or '(untitled)'}** [{resource.kind}]",
        f"ID: {resource.id}",
    ]
    if resource.url:
        lines.append(f"URL: {resource.url}")
    if resource.tags:
        tag_names = ", ".join(t.name for t in resource.tags if t.name)
        if tag_names:
            lines.append(f"Tags: {tag_names}")
    if resource.created_at:
        lines.append(f"Created: {resource.created_at}")
    if resource.parent_id:
        lines.append(f"Parent: {resource.parent_id}")
    return "\n".join(lines)


@mcp.tool()
async def list_resources(
    ctx: Context,
    kind: list[str] | None = None,
    parent_id: str | None = None,
    root_id: str | None = None,
    tag_ids: list[str] | None = None,
    name: str | None = None,
    limit: int = 20,
) -> str:
    """Browse and filter Fabric resources.

    Args:
        kind: Filter by types (notepad, bookmark, document, folder, image, etc.)
        parent_id: Filter by parent folder (UUID or alias like @alias::inbox)
        root_id: Filter by root container ID
        tag_ids: Filter by tag IDs
        name: Filter by name (partial match)
        limit: Max results (default 20)
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        page = await client.filter_resources(
            kind=kind,
            parent_id=parent_id,
            root_id=root_id,
            tag_ids=tag_ids,
            name=name,
            limit=limit,
        )
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    if not page.items:
        return "No resources found matching filters."
    lines = [f"Found {page.total or len(page.items)} resources:\n"]
    for r in page.items:
        lines.append(f"- **{r.name or '(untitled)'}** [{r.kind}] id={r.id}")
        if r.url:
            lines.append(f"  URL: {r.url}")
    if page.has_more:
        lines.append("\n(More results available — increase limit or refine filters)")
    return "\n".join(lines)


@mcp.tool()
async def list_tags(
    ctx: Context,
    name: str | None = None,
) -> str:
    """List available Fabric tags. Use tag IDs to filter searches and resources.

    Args:
        name: Filter tags by name (partial match)
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        tags = await client.list_tags(name=name)
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    if not tags:
        return "No tags found."
    lines = ["Fabric tags:\n"]
    for tag in tags:
        lines.append(f"- **{tag.name}** id={tag.id}")
    return "\n".join(lines)


# --- Notepad Content Tool ---


@mcp.tool()
async def get_notepad_content(resource_id: str, ctx: Context) -> str:
    """Read the text content of a Fabric notepad.

    Args:
        resource_id: The notepad resource UUID
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        content = await client.get_notepad_content(resource_id)
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    return content if content else "(empty notepad)"


# --- Content Creation Tools ---


@mcp.tool()
async def create_bookmark(
    url: str,
    parent_id: str,
    ctx: Context,
    name: str | None = None,
    tags: list[str] | None = None,
    comment: str | None = None,
) -> str:
    """Save a URL as a bookmark in Fabric.

    Args:
        url: The URL to bookmark
        parent_id: Where to save (folder UUID or alias like @alias::inbox)
        name: Display name (auto-generated from URL if omitted)
        tags: Tag names to apply (created automatically if new)
        comment: Optional note about this bookmark
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    tag_dicts = [{"name": t} for t in tags] if tags else None
    try:
        resource = await client.create_bookmark(
            url=url,
            parent_id=parent_id,
            name=name,
            tags=tag_dicts,
            comment=comment,
        )
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    return f"Bookmark created: **{resource.name or url}** (id={resource.id})"


@mcp.tool()
async def create_notepad(
    parent_id: str,
    ctx: Context,
    name: str | None = None,
    text: str | None = None,
    tags: list[str] | None = None,
    comment: str | None = None,
) -> str:
    """Create a new notepad (note) in Fabric.

    Args:
        parent_id: Where to create (folder UUID or alias like @alias::inbox)
        name: Notepad title
        text: Plain text content
        tags: Tag names to apply (created automatically if new)
        comment: Optional note about this notepad
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    tag_dicts = [{"name": t} for t in tags] if tags else None
    try:
        resource = await client.create_notepad(
            parent_id=parent_id,
            name=name,
            text=text,
            tags=tag_dicts,
            comment=comment,
        )
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    return f"Notepad created: **{resource.name or '(untitled)'}** (id={resource.id})"


@mcp.tool()
async def create_folder(
    parent_id: str,
    ctx: Context,
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Create a folder in Fabric for organizing content.

    Args:
        parent_id: Where to create (root/folder UUID or alias like @alias::inbox)
        name: Folder name
        description: Optional description
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        resource = await client.create_folder(
            parent_id=parent_id,
            name=name,
            description=description,
        )
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    return f"Folder created: **{resource.name or '(untitled)'}** (id={resource.id})"


# --- Delete Resources Tool ---


@mcp.tool()
async def delete_resources(
    resource_ids: list[str],
    ctx: Context,
    archive: bool = False,
) -> str:
    """Delete or archive Fabric resources.

    Args:
        resource_ids: List of resource UUIDs to delete
        archive: If true, archive instead of permanent delete (recoverable via Fabric UI)
    """
    client: FabricClient = ctx.request_context.lifespan_context["client"]
    try:
        await client.delete_resources(resource_ids, archive=archive)
    except FabricAPIError as e:
        raise ToolError(_format_api_error(e)) from e
    action = "Archived" if archive else "Deleted"
    return f"{action} {len(resource_ids)} resource(s)."
