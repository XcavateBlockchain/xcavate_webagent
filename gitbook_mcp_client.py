# gitbook_mcp_client.py - HTTP client for GitBook MCP at doc-hub.xcavate.io
"""
HTTP-based client for the GitBook MCP server at https://doc-hub.xcavate.io/~gitbook/mcp

This server uses JSON-RPC over HTTP POST with SSE-formatted responses.

Available tools:
- searchDocumentation(query): Search across documentation
- getPage(url): Fetch full markdown content of a specific page
"""

import json
import requests
from typing import List, Dict, Any


GITBOOK_MCP_URL = "https://doc-hub.xcavate.io/~gitbook/mcp"


def _send_mcp_request(method: str, params: dict, request_id: int = 1) -> Any:
    """Send a JSON-RPC request to the GitBook MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    response = requests.post(GITBOOK_MCP_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    # The server returns SSE-formatted responses (event: message\ndata: {...})
    content = response.text.strip()

    # Parse SSE format to extract JSON
    if content.startswith("event: message"):
        # Extract the data line and parse JSON
        for line in content.split("\n"):
            if line.startswith("data: "):
                json_str = line[6:]  # Remove "data: " prefix
                return json.loads(json_str)

    # Fallback: try parsing as direct JSON
    return json.loads(content)


def _parse_tool_result(result: dict) -> str:
    """Parse MCP tool result into a readable string."""
    if "error" in result:
        return f"Error: {result['error'].get('message', 'Unknown error')}"

    if "result" not in result:
        return "No result returned."

    tool_result = result["result"]
    if "content" not in tool_result or len(tool_result["content"]) == 0:
        return "No content found."

    # Parse content array - each item has type and text
    parts = []
    for item in tool_result["content"]:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(item.get("text", ""))
        elif hasattr(item, 'text'):
            parts.append(item.text)

    if not parts:
        return str(tool_result)

    return "\n\n---\n\n".join(parts)


def search_documentation(query: str) -> str:
    """
    Search across the documentation to find relevant information.

    Args:
        query: The search query (keywords or natural language question)

    Returns:
        Formatted search results with titles, content snippets, and links
    """
    # Use tools/call method as per MCP spec
    result = _send_mcp_request("tools/call", {
        "name": "searchDocumentation",
        "arguments": {"query": query}
    })
    return _parse_tool_result(result)


def get_page(url: str) -> str:
    """
    Fetch the full markdown content of a specific documentation page.

    Args:
        url: The URL of the page (e.g., https://doc-hub.xcavate.io/getting-started)

    Returns:
        Full markdown content of the page
    """
    # Use tools/call method as per MCP spec
    result = _send_mcp_request("tools/call", {
        "name": "getPage",
        "arguments": {"url": url}
    })
    return _parse_tool_result(result)


def list_tools() -> List[str]:
    """List available tools on the GitBook MCP server."""
    result = _send_mcp_request("tools/list", {})

    if "result" in result and "tools" in result["result"]:
        return [tool["name"] for tool in result["result"]["tools"]]
    return []


def search_documentation_sync(query: str) -> str:
    """
    Synchronous wrapper for search_documentation (alias for compatibility).

    Args:
        query: The search query

    Returns:
        Formatted search results
    """
    return search_documentation(query)


def get_mcp_status() -> dict:
    """
    Check if the GitBook MCP server is available.

    Returns:
        Dictionary with 'available' status and server info
    """
    try:
        tools = list_tools()
        return {
            "available": True,
            "provider": "GitBook MCP (doc-hub.xcavate.io)",
            "tools": tools
        }
    except Exception as e:
        return {
            "available": False,
            "reason": str(e),
            "provider": None
        }


if __name__ == "__main__":
    print("GitBook MCP Client Test")
    print("=" * 50)

    status = get_mcp_status()
    print(f"Status: {status}")

    if status["available"]:
        print("\nTesting search...")
        result = search_documentation("what is xcavate")
        print(f"\nSearch result:\n{result[:500]}...")
