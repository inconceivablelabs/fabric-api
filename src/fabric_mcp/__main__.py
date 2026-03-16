"""Entry point: python -m fabric_mcp"""

from fabric_mcp.server import mcp

mcp.run(transport="stdio")
