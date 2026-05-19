"""Vercel serverless function: Documentation search endpoint."""
import json
from gitbook_mcp_client import search_documentation


def handler(request):
    """Handle POST /api/web-search requests."""
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        body = request.get_json() or {}
        query = body.get("query", "")

        if not query:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing query parameter"})
            }

        results = search_documentation(query)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"query": query, "results": results})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
