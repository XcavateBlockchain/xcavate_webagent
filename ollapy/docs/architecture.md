# Architecture Details

## Backend (Python)

### server.py
Flask application providing:
- **GET /** - Serves index.html
- **GET /css/* , GET /js/** - Static assets
- **POST /api/chat** - Streaming chat endpoint (NDJSON)
- **GET /api/chats** - List all chats
- **POST /api/chats** - Save a chat
- **GET /api/chats/<id>** - Get a specific chat
- **DELETE /api/chats/<id>** - Delete a chat
- **POST /api/web-search** - Web search via MCP
- **GET /api/mcp-status** - MCP connection status

### langgraph_agent.py
Core agent logic:

**System Prompt**: Defines AI behavior as RealXmarket support assistant. Instructs to use `search_realxmarket_docs` tool automatically when unsure.

**Tools**:
- `search_realxmarket_docs(query: str) -> str` - Searches RealXmarket documentation

**Streaming Flow**:
1. Convert incoming message dicts to LangChain message objects
2. Add system prompt if not present
3. Invoke LLM with tools bound
4. If tool call detected:
   - Execute tool
   - Log to console (for debugging)
   - Add AI message + tool response to context
   - Stream final answer
5. If no tool call: stream response directly

**Key Functions**:
- `create_llm_with_tools(model)` - Returns ChatOpenAI with tool binding
- `ai_node(state, llm)` - LLM reasoning step
- `tool_node(state)` - Tool execution step
- `final_answer_node(state, llm)` - Final response after tool use
- `stream_agent_response(messages, model)` - Main streaming entry point

## Frontend (JavaScript)

### js/config.js
Configuration constants:
- `DEFAULT_MODEL = "gpt-4o"`
- `MAX_CONTEXT_WINDOW = 8192`

### js/api.js
API client module:
- `streamAgentResponse(history, model, onChunk, onDone, signal)` - Streams chat responses
- Includes embedded system prompt (should match backend)
- Handles NDJSON parsing from server

### js/state.js
Client-side state:
- Active chat ID
- Current chat history
- Current model
- Attachments (file uploads)
- Model context windows

### js/ui.js
DOM manipulation:
- `addMessageToLog(role, content)` - Render message in chat
- `renderInlineQuickReplies(replies, onSelect)` - Show follow-up suggestions
- `bindQuickStartActions(onSelect)` - Bind quick action buttons
- `updateTokenUI(count, max)` - Update token counter
- `showLanding()`, `showChat()` - View navigation

### js/app.js
Main application:
- Event handlers for form submit, quick actions
- `handleFormSubmit(event)` - Process user input
- `submitQuickAction(promptText)` - Handle quick action clicks
- `streamAgentResponse()` integration
- Error handling and loading states

## Message Format

**Request Body**:
```json
{
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "What is KYC?" },
    { "role": "assistant", "content": "..." }
  ],
  "model": "gpt-4o"
}
```

**Response Format** (NDJSON):
```
{"message": {"content": "To"}, "done": false}
{"message": {"content": " complete"}, "done": false}
{"message": {"content": " KYC..."}, "done": false}
{"done": true}
```

## Tool Integration

The `realxmarket_docs` package provides:
- `initialize_docs()` - Initialize documentation index
- `search_and_answer(query)` - Search and return relevant info
- `get_docs_status()` - Check if docs are available

Tool calls are logged to server console:
```
[TOOL CALL] search_realxmarket_docs with query: "How to recover account?"

[TOOL RESPONSE] Found documentation about account recovery...
```
