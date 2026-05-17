# RealXmarket Web Assistant Documentation

Quick reference for working with this project.

## Start Here

- **[project-overview.md](./project-overview.md)** - What the project is, tech stack, architecture overview
- **[architecture.md](./architecture.md)** - Detailed request flow, file purposes, message formats
- **[api-reference.md](./api-reference.md)** - All API endpoints and frontend module signatures
- **[development-guide.md](./development-guide.md)** - How to add features, debug, common tasks
- **[components.md](./components.md)** - UI components, data models, event flows
- **[system-prompt.md](./system-prompt.md)** - Current system prompt and how to modify it

## Quick Commands

```bash
# Run the server
python server.py  # defaults to port 8001

# Check tool logs
# Look at terminal output for [TOOL CALL] and [TOOL RESPONSE]

# View chat history
ls logs/
```

## Environment

```bash
export OPENAI_API_KEY="sk-..."
```

## Key Files

| File | Edit When... |
|------|--------------|
| `langgraph_agent.py` | Adding tools, changing agent logic |
| `server.py` | Adding API endpoints, Flask config |
| `js/app.js` | Adding UI interactions, event handlers |
| `js/api.js` | Changing API calls, system prompt |
| `js/config.js` | Updating model, context size |
| `index.html` | Adding new UI elements |

## Troubleshooting

**Streaming not working?**
- Check `stream_mode="tokens"` in langgraph_agent.py
- Verify OpenAI API key is set
- Check browser console for errors

**Tool not being called?**
- Verify tool is bound to LLM with `bind_tools()`
- Check system prompt instructs tool usage
- Look for `[TOOL CALL]` in server console

**Messages duplicated?**
- Check event handlers have `preventDefault()` and `stopPropagation()`
- Verify quick actions don't trigger multiple times
