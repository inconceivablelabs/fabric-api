# Fabric API

[![Semgrep](https://github.com/inconceivablelabs/fabric-api/actions/workflows/semgrep.yml/badge.svg)](https://github.com/inconceivablelabs/fabric-api/actions/workflows/semgrep.yml)

Python client library and MCP server for the [Fabric](https://fabric.so) v2 REST API.

Fabric is a self-organizing workspace and knowledge management app. This project provides:

1. **`fabric_client`** -- async Python library wrapping the Fabric REST API
2. **`fabric_mcp`** -- MCP server exposing Fabric to Claude Desktop/Code

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras
```

### Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `FABRIC_API_KEY` | Yes | Fabric API key (get from Fabric app settings, Pro tier required) |
| `FABRIC_BASE_URL` | No | Override API base URL (default: `https://api.fabric.so/v2`) |

## Using the Client Library

```python
from fabric_client import FabricClient

# Async
async with FabricClient(api_key="...") as client:
    results = await client.search("my query")
    roots = await client.list_roots()
    await client.create_notepad(parent_id="@alias::inbox", name="Hello", text="World")

# Sync (for scripts/notebooks)
from fabric_client import FabricSyncClient

client = FabricSyncClient(api_key="...")
results = client.search("my query")
client.close()
```

## MCP Server

### Running

```bash
# Direct
uv run python -m fabric_mcp

# Or via MCP CLI
uv run mcp run fabric_mcp.server:mcp
```

### Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fabric": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fabric-api", "python", "-m", "fabric_mcp"],
      "env": {
        "FABRIC_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `search` | Search content (semantic + keyword) |
| `list_roots` | List root containers (inbox, spaces) |
| `get_resource` | Get resource details by ID |
| `list_resources` | Browse/filter resources by type, location, tags |
| `get_notepad_content` | Read notepad text content |
| `create_bookmark` | Save a URL as bookmark |
| `create_notepad` | Create a note |
| `create_folder` | Create a folder |
| `delete_resources` | Delete or archive resources |
| `list_tags` | List available tags |

## Development

```bash
# Run tests
uv run pytest -v

# Linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Type checking
uv run pyright src/
```
