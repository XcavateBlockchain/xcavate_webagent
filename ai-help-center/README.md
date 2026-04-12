# Local AI Help Center

Mobile-first single-page AI help center UI with a local backend proxy to Ollama.

## Run

1. Make sure Ollama is running locally on `http://localhost:11434` and has a model pulled, for example:
   - `ollama pull llama3`
2. Start the local web server:
   - `python3 server.py`
3. Open in browser:
   - `http://127.0.0.1:3000`

## Optional environment variables

- `PORT` (default `3000`)
- `OLLAMA_URL` (default `http://localhost:11434/api/generate`)
- `OLLAMA_MODEL` (default `llama3`)

Example:

```bash
OLLAMA_MODEL=mistral PORT=8080 python3 server.py
```
