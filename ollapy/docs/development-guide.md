# Development Guide

## Adding a New Tool

1. Define the tool function with `@tool` decorator in `langgraph_agent.py`:

```python
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

Edit `SYSTEM_PROMPT` in `langgraph_agent.py` AND `SYSTEM_PROMPT` constant in `js/api.js`. They should match.

**Important**: The system prompt controls AI behavior. Be specific about:
- What the AI should/w shouldn't do
- When to use tools
- Tone and style guidelines
- Error handling instructions

---

## Adding a New UI Feature

1. Add HTML markup to `index.html`
2. Export the element in `js/ui.js` `dom` object
3. Add event handlers in `js/app.js` or bind them in `init()`

**Example - Adding a settings button**:

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

1. **Manual testing**: Use the UI to test common flows
2. **Tool testing**: Check server console for tool call/response logs
3. **Streaming**: Verify tokens appear gradually (not all at once)
4. **Error handling**: Test with invalid API key, network issues

---

## Dependencies

**Python** (`requirements.txt`):
- `Flask` - Web server
- `langchain` - LLM framework
- `langgraph` - Agent workflows
- `langchain-openai` - OpenAI integration
- `realxmarket_docs` - Documentation search (external package)

**JavaScript** (no npm, vanilla JS):
- External CDN libs: `marked`, `DOMPurify`

---

## File Structure

```
ollapy/
├── server.py              # Flask backend
├── langgraph_agent.py     # Agent logic
├── requirements.txt       # Python deps
├── index.html            # Main HTML
├── css/
│   └── style.css         # Styles
├── js/
│   ├── app.js            # Main app logic
│   ├── api.js            # API client
│   ├── config.js         # Config constants
│   ├── state.js          # State management
│   └── ui.js             # UI helpers
└── docs/                 # This documentation
    ├── project-overview.md
    ├── architecture.md
    ├── api-reference.md
    └── development-guide.md
```
