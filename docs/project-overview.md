# RealXmarket Web Assistant - Project Overview

## What This Project Is

A customer support chat assistant for RealXmarket, built with a Flask backend and vanilla JavaScript frontend. The AI uses OpenAI's GPT-4o and has access to RealXmarket documentation via a tool integration.

## Tech Stack

- **Backend**: Python Flask + LangGraph + LangChain (OpenAI)
- **Frontend**: Vanilla JavaScript (ES6 modules)
- **LLM**: OpenAI GPT-4o
- **Tools**: RealXmarket documentation search (`realxmarket_docs` package)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser       │────▶│   Flask Server   │────▶│   OpenAI API    │
│   (index.html)  │◀────│   (server.py)    │◀────│   (gpt-4o)      │
│                 │     │                  │     │                 │
│   js/app.js     │     │ langgraph_agent  │────▶│ realxmarket     │
│   js/api.js     │     │                  │     │ docs (tool)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Request Flow

1. User types a question or clicks a quick action button
2. Frontend sends POST to `/api/chat` with messages array
3. Flask routes to `langgraph_agent.stream_agent_response()`
4. Agent converts messages, adds system prompt
5. LLM is invoked - may call `search_realxmarket_docs` tool if needed
6. If tool is called: tool executes → result added to context → final response streamed
7. Response is streamed back as NDJSON (newline-delimited JSON)
8. Frontend renders streaming tokens in real-time

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | Flask server, API endpoints, static file serving |
| `langgraph_agent.py` | Agent logic, tool definition, streaming handler |
| `js/app.js` | Main application logic, event handlers |
| `js/api.js` | HTTP client, system prompt, streaming API |
| `js/config.js` | Configuration (model name, context window) |
| `js/state.js` | Client-side state management |
| `js/ui.js` | DOM manipulation, rendering helpers |
| `index.html` | Single-page application markup |

## Environment Variables

```bash
OPENAI_API_KEY=sk-...  # Required for OpenAI API access
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
