# Development Guide

## Adding a New Tool

1. Define the tool function with `@tool` decorator in `langgraph_agent.py`:

```python
from langchain_core.tools import tool

@tool
def my_new_tool(query: str) -> str:
    """Description of what the tool does. The LLM uses this to decide when to call it."""
    # Your implementation here
    return result
```

2. Add the tool to the LLM binding:

```python
def create_llm_with_tools(model_name: str = "gpt-4o"):
    llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=api_key)
    return llm.bind_tools([search_realxmarket_docs, my_new_tool])  # Add new tool
```

3. Handle the tool call in `stream_agent_response()`:

```python
if func_name == "my_new_tool":
    args = tool_call.get("args", {})
    query = args.get("query", "")
    result = my_new_tool.invoke(query)
    # Add to context and continue
```

---

## Modifying the System Prompt

Edit `SYSTEM_PROMPT` in `langgraph_agent.py`. The prompt controls AI behavior and tool usage.

**Important**: The system prompt controls AI behavior. Be specific about:
- What the AI should/w shouldn't do
- When to use tools
- Tone and style guidelines
- Error handling instructions

### Example Modifications

**To change tone:**
Adjust "friendly, professional tone" to desired style (e.g., "casual and conversational", "formal and technical")

**To add capabilities:**
Add new guidelines like:
- "When users ask about troubleshooting, provide step-by-step instructions"
- "Include relevant links from the documentation when possible"

**To restrict behavior:**
Add negative constraints:
- "Do not provide financial or investment advice"
- "Do not speculate about future features or roadmaps"

See [`system-prompt.md`](system-prompt.md) for full reference.

---

## Adding a New UI Feature

1. Add HTML markup to `index.html`
2. Export the element in `js/ui.js` `dom` object
3. Add event handlers in `js/app.js` or bind them in `init()`

**Example - Adding a settings button:**

```html
<!-- index.html -->
<button id="settings-btn">Settings</button>
```

```javascript
// js/ui.js
export const dom = {
  // ... existing
  settingsBtn: document.getElementById('settings-btn'),
}
```

```javascript
// js/app.js
ui.dom.settingsBtn.addEventListener('click', () => {
  // Your logic here
});
```

---

## Debugging

**Server-side**: Check terminal output for:
- `[TOOL CALL]` and `[TOOL RESPONSE]` logs
- Flask request logs
- Python tracebacks

**Client-side**: Open browser DevTools Console for:
- `console.log()` statements from app.js
- Network tab for API requests/responses
- Errors from try/catch blocks

---

## Common Tasks

### Change the AI Model
Update `DEFAULT_MODEL` in `js/config.js` and default parameters in Python files.

### Adjust Context Window Size
Update `MAX_CONTEXT_WINDOW` in `js/config.js`.

### Add Quick Action Buttons
Add buttons in `index.html` with `data-prompt` attribute:
```html
<button class="quick-action-btn" data-prompt="How do I recover my account?">
  Recover Account
</button>
```

### Modify Token Counter Behavior
Edit `estimateTokens()` and `updateTotalTokenCount()` in `js/app.js`.

---

## Testing

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_realxmarket_docs.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Structure

-   `tests/test_realxmarket_docs.py` - Documentation search module tests
-   `tests/test_server.py` - Flask API endpoint tests
-   `tests/test_langgraph_agent.py` - Agent logic and tool tests
-   `tests/conftest.py` - Shared fixtures and mocks

### Manual Testing

1. **Common flows**: Use the UI to test chat creation, loading, deletion
2. **Tool calls**: Check server console for tool call/response logs
3. **Streaming**: Verify tokens appear gradually (not all at once)
4. **Error handling**: Test with invalid API key, network issues

---

## Dependencies

**Python** (`requirements.txt`):
- `Flask` - Web framework
- `langchain` - LLM orchestration
- `langgraph` - Agent workflows
- `langchain-openai` - OpenAI integration
- `requests` - HTTP client
- `xmltodict` - XML parsing

**JavaScript** (no npm, vanilla JS):
- External CDN libs: `marked`, `DOMPurify`

---

## File Structure

```
xcavate-web-assistant/
├── server.py              # Flask backend
├── langgraph_agent.py     # Agent logic with LangGraph
├── realxmarket_docs.py    # Documentation search client
├── requirements.txt       # Python dependencies
├── index.html            # Main HTML (SPA)
├── css/
│   └── style.css         # Styles
├── js/
│   ├── app.js            # Main application logic
│   ├── api.js            # API client & streaming
│   ├── config.js         # Configuration constants
│   ├── state.js          # State management
│   └── ui.js             # UI rendering helpers
├── logs/                 # Chat history storage
├── tests/                # Unit test suite
│   ├── conftest.py
│   ├── test_server.py
│   ├── test_langgraph_agent.py
│   └── test_realxmarket_docs.py
└── docs/                 # Documentation
    ├── project-overview.md
    ├── architecture.md
    ├── api-reference.md
    ├── components.md
    ├── development-guide.md
    └── system-prompt.md
```

---

## Git Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -am "Add my feature"`
3. Run tests: `pytest tests/ -v`
4. Push and create PR: `git push origin feature/my-feature`
