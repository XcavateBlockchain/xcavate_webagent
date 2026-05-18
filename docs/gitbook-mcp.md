# GitBook MCP Integration

## Overview

The RealXmarket Web Assistant uses the GitBook Model Context Protocol (MCP) server at `https://doc-hub.xcavate.io/~gitbook/mcp` for documentation search. This provides real-time access to the official RealXmarket documentation without needing to crawl or index pages locally.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   LangGraph     │────▶│   gitbook_mcp    │────▶│   GitBook MCP   │
│   Agent         │     │   client.py      │     │   Server        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                   doc-hub.xcavate.io
```

## MCP Tools

The GitBook MCP server exposes two tools:

### `searchDocumentation(query)`

Searches across the documentation for relevant information.

**Usage:**
```python
from gitbook_mcp_client import search_documentation

result = search_documentation("how to connect wallet")
print(result)
```

### `getPage(url)`

Fetches the full markdown content of a specific documentation page.

**Usage:**
```python
from gitbook_mcp_client import get_page

content = get_page("https://doc-hub.xcavate.io/getting-started")
print(content)
```

## Client Implementation

The `gitbook_mcp_client.py` module provides a simple HTTP-based client that communicates with the GitBook MCP server using JSON-RPC over POST requests.

**Key functions:**
- `search_documentation(query)` - Search docs and return results
- `get_page(url)` - Fetch full page content
- `list_tools()` - List available MCP tools
- `get_mcp_status()` - Check connection status

## Running Tests

```bash
pytest tests/test_server.py -v
```

## Troubleshooting

If the MCP connection fails, check:
1. Network connectivity to `doc-hub.xcavate.io`
2. The server responds at `https://doc-hub.xcavate.io/~gitbook/mcp`
3. Firewall rules allowing HTTPS traffic
