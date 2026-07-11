# RealXmarket Web Assistant - Project Overview

## What This Project Is

A customer support chat assistant for RealXmarket, built with a Flask backend and vanilla JavaScript frontend. The AI uses OpenAI's GPT-4o and has automatic access to RealXmarket documentation via a tool integration for accurate, up-to-date answers.

## Tech Stack

-   **Backend**: Python Flask + LangGraph + LangChain (OpenAI)
-   **Frontend**: Vanilla JavaScript (ES6 modules)
-   **LLM**: OpenAI GPT-4o
-   **Tools**: RealXmarket documentation search (`realxmarket_docs` package)
-   **Testing**: pytest

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser       │────▶│   Flask Server   │────▶│   OpenAI API    │
│   (index.html)  │◀────│   (server.py)    │◀────│   (gpt-4o)      │
│                 │     │                  │     │                 │
│   js/app.js     │     │ langgraph_agent  │────▶│ realxmarket     │
│   js/api.js     │     │                  │     │ docs (tool)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                          │
                          ▼
                   ┌──────────────────┐
                   │  Documentation   │
                   │  (doc-hub.xcavate.io) │
                   └──────────────────┘
```

## Request Flow

1.  User types a question or clicks a quick action button
2.  Frontend sends POST to `/api/chat` with messages array
3.  Flask routes to `langgraph_agent.stream_agent_response()`
4.  Agent converts messages, adds system prompt
5.  LLM is invoked - may call `search_realxmarket_docs` tool if needed
6.  If tool is called:
    - Tool executes documentation search
    - Result added to context
    - Final response streamed
7.  Response is streamed back as NDJSON (newline-delimited JSON)
8.  Frontend renders streaming tokens in real-time with Markdown formatting

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | Flask server, API endpoints, static file serving |
| `langgraph_agent.py` | Agent logic, tool definition, streaming handler |
| `realxmarket_docs.py` | Documentation search client (sitemap indexer) |
| `js/app.js` | Main application logic, event handlers |
| `js/api.js` | HTTP client, system prompt, streaming API |
| `js/state.js` | Client-side state management |
| `js/ui.js` | DOM manipulation, rendering helpers |
| `index.html` | Single-page application markup |
| `tests/` | Unit test suite (pytest) |

## Environment Variables

```bash
OPENAI_API_KEY=sk-...  # Required for OpenAI API access
OPENAI_MODEL=gpt-4o
MAX_CONTEXT_WINDOW=8192
```

## Running the Project

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY="your-key-here"

# Run server
python server.py [port]  # defaults to 8001
```

Then open `http://localhost:8001` in your browser.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_realxmarket_docs.py -v
pytest tests/test_server.py -v
pytest tests/test_langgraph_agent.py -v
```

See [`README.md`](../README.md#testing) for more details.
