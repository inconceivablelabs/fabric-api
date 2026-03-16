# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Two-package project:**
1. **`fabric_client`** — async Python library wrapping the Fabric (fabric.so) v2 REST API
2. **`fabric_mcp`** — MCP server exposing `fabric_client` to Claude Desktop/Code

Fabric is a self-organizing workspace and knowledge management app for organizing prompts, ideas, and documents.

## Fabric API Reference

- **OpenAPI spec:** `fabric-openapi.yaml` (local) or `https://api.fabric.so/v2/openapi/public.yaml`
- **Base URL:** `https://api.fabric.so/v2`
- **Auth:** `X-Api-Key` header (API key from Fabric app settings, Pro tier required)
- **Workspace header:** `X-Fabric-Workspace-Id` (optional, for delegated workspaces)

**Core concepts:**
- **Resources:** Base entity — bookmarks, images, folders, notes, files, etc. Discriminated by `kind` field.
- **Resource Roots:** Top-level containers (SYSTEM/inbox/bin, SPACE, INTEGRATION)
- **Parent ID:** UUID or alias (`@alias::inbox`, `@alias::bin`)
- **Search:** `POST /v2/search` with `mode: "hybrid"` (semantic + keyword)
- **Pagination:** Filter uses cursor-based (`nextCursor`), Search uses page-based (`page`/`pageSize`)
- **Delete:** `POST /v2/resources/delete` (batch, not HTTP DELETE)
- **File upload:** Two-step: `GET /v2/upload` for presigned URL → PUT file → `POST /v2/files`

The API is beta — expect breaking changes. Verify against the OpenAPI spec.

**Known API quirks (verified Feb 2026):**
- List endpoints (`GET /resource-roots`, `GET /tags`) wrap responses in `{count, data: {<plural>: [...]}}` envelopes — not bare arrays as the OpenAPI spec implies
- `GET /upload` requires `size` param despite the spec marking it optional (server defaults to `NaN` and rejects)
- `POST /tags` returns 401 with API key auth — tag creation is handled implicitly by passing `tags: [{"name": "..."}]` to resource create endpoints instead. `create_tag` removed from client.

## Tech Stack

- **Python 3.12+** with `uv` for dependency management
- **httpx** for async HTTP
- **pydantic >= 2.0** for response models
- **mcp[cli] >= 1.0** for MCP server (FastMCP)
- **pytest** + `pytest-asyncio` + `respx` for testing
- **ruff** for linting/formatting, **pyright** for type checking

## Common Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run a single test file
uv run pytest tests/test_exceptions.py -v

# Run a single test
uv run pytest tests/test_http.py::test_404_raises_not_found -v

# Linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Type checking
uv run pyright src/
```

## Architecture

```
src/fabric_client/                  # API client library
├── __init__.py             # Public API exports
├── client.py               # FabricClient — single entry point, all API methods
├── http.py                 # Async HTTP transport (auth, retries, error mapping)
├── models.py               # Pydantic response models (extra="allow" for forward compat)
├── exceptions.py           # Typed exception hierarchy
└── _compat.py              # FabricSyncClient — sync wrapper for scripts/notebooks

src/fabric_mcp/                     # MCP server
├── __init__.py             # Exports mcp server instance
├── server.py               # FastMCP server, lifespan, 10 tools, error handling
└── __main__.py             # Entry point: python -m fabric_mcp

tests/
├── conftest.py             # Shared fixtures (api_key, base_url)
├── test_exceptions.py      # Exception hierarchy tests
├── test_models.py          # Pydantic model tests
├── test_http.py            # HTTP layer tests (auth, errors, retries)
├── test_client_resources.py # FabricClient resource root/resource tests
├── test_client_content.py  # FabricClient search/bookmark/notepad/folder/tag tests
├── test_client_files.py    # FabricClient file upload tests
├── test_sync_client.py     # FabricSyncClient wrapper tests
└── mcp/
    ├── conftest.py         # MCP test fixtures (in-process client factory)
    └── test_server.py      # MCP tool tests (19 tests)
```

**Key decisions:**
- Async-first with sync adapter (not the other way around)
- Thin wrapper mirroring the REST API — no domain abstractions
- Pydantic models with `extra="allow"` so unknown API fields pass through
- Env-var configuration (`FABRIC_API_KEY`, `FABRIC_BASE_URL`) — no config files
- Fail-open on reads, fail-loud on writes
- Stateless — no local caching

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `FABRIC_API_KEY` | Yes | Fabric API key (get from Fabric app settings) |
| `FABRIC_BASE_URL` | No | Override API base URL (default: `https://api.fabric.so/v2`) |

## Testing Approach

**TDD throughout.** Each feature follows: write failing test → implement → verify passing → commit.

- Unit tests use `respx` to mock httpx responses — tests exercise the real client against mocked HTTP
- MCP tests use `create_connected_server_and_client_session` from `mcp.shared.memory` for in-process testing
- Integration tests marked `@pytest.mark.integration` (require real API key, skipped by default)
- No mocking of internal client classes — always test through the public API
