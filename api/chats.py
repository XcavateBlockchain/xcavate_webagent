"""Vercel serverless function: Chat history management endpoint.

Note: This endpoint is not functional on Vercel due to ephemeral filesystem.
Chat history storage requires an external database (PostgreSQL, Redis, etc.)
"""
import json


def handler(request):
    """Handle GET/POST /api/chats requests."""
    if request.method == "GET":
        return {
            "statusCode": 501,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Chat history storage not available on serverless platforms",
                "chats": []
            })
        }

    elif request.method == "POST":
        return {
            "statusCode": 501,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Chat history persistence not available on serverless platforms"
            })
        }

    else:
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }
