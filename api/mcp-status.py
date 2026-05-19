"""Vercel serverless function: GitBook MCP status endpoint."""
import json
from gitbook_mcp_client import get_mcp_status


def handler(request):
    """Handle GET /api/mcp-status requests."""
    try:
        status = get_mcp_status()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(status)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"available": False, "reason": str(e)})
        }
