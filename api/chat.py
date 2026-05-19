"""Vercel serverless function: Chat streaming endpoint."""
import json
from langgraph_agent import stream_agent_response


def handler(request):
    """Handle POST /api/chat requests with streaming response."""
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        body = request.get_json() or {}
        messages = body.get("messages", [])
        model = body.get("model", "gpt-4o")

        def generate():
            try:
                for event in stream_agent_response(messages, model):
                    if "messages" in event:
                        last_msg = event["messages"][-1]
                        if hasattr(last_msg, 'content'):
                            content = last_msg.content
                        elif isinstance(last_msg, dict):
                            content = last_msg.get("content", "")
                        else:
                            content = ""

                        if content:
                            chunk = {"message": {"content": content}, "done": False}
                            yield json.dumps(chunk) + "\n"

                    yield json.dumps({"done": event.get("done", False)}) + "\n"

            except Exception as e:
                yield json.dumps({"error": str(e), "done": True}) + "\n"

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/x-ndjson",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            },
            "body": generate()
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
