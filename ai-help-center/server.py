#!/usr/bin/env python3
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PORT = int(os.getenv("PORT", "3000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
PUBLIC_DIR = Path(__file__).parent / "public"


class HelpCenterHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

        length_header = self.headers.get("Content-Length")
        if not length_header:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing request body."})
            return

        try:
            length = int(length_header)
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body."})
            return

        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Prompt is required."})
            return

        system_context = (
            "You are a helpful customer service AI for the Real X Market platform. "
            "Use current and practical information, ask clarifying questions when needed, "
            "and provide concise step-by-step support guidance."
        )

        ollama_payload = {
            "model": OLLAMA_MODEL,
            "prompt": f"{system_context}\\n\\nUser question: {prompt}",
            "stream": False,
        }

        try:
            request = Request(
                OLLAMA_URL,
                data=json.dumps(ollama_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=90) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            self._send_json(
                HTTPStatus.BAD_GATEWAY,
                {
                    "error": "Failed to reach local Ollama instance.",
                    "details": details,
                },
            )
            return
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "error": "Unexpected server error while querying Ollama.",
                    "details": str(error),
                },
            )
            return

        answer = str(data.get("response", "I could not generate a response.")).strip()
        self._send_json(HTTPStatus.OK, {"answer": answer, "model": OLLAMA_MODEL})

    def do_GET(self):
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "model": OLLAMA_MODEL})
            return

        if self.path in ("/", ""):
            self.path = "/index.html"

        return super().do_GET()

    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), HelpCenterHandler)
    print(f"AI Help Center listening on http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
