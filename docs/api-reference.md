# API Reference

## Backend Endpoints

### POST /api/chat
Stream a chat response from the AI.

**Request:**
```json
{
  "messages": [
    { "role": "user", "content": "How do I reset my password?" },
    { "role": "assistant", "content": "I can help with that..." }
  ],
  "model": "gpt-4o"
}
```

**Response:** Streaming NDJSON (newline-delimited JSON)
```
{"message": {"content": "To"}, "done": false}
{"message": {"content": " reset"}, "done": false}
{"message": {"content": " your password..."}, "done": false}
{"done": true}
```

**Error Response:**
```
{"error": "Error message here", "done": true}
```

---

### GET /api/chats
List all saved chats.

**Response:**
```json
[
  { "id": "1234567890", "title": "How to reset password..." },
  { "id": "1234567889", "title": "Transaction issues" }
]
```

---

### POST /api/chats
Save a new chat or update an existing one.

**Request:**
```json
{
  "id": "1234567890",
  "title": "Password reset help",
  "history": [...],
  "model": "gpt-4o"
}
```

**Response:**
```json
{ "success": true, "id": "1234567890" }
```

---

### GET /api/chats/<chat_id>
Get a specific chat by ID.

**Response:** Full chat data JSON

---

### DELETE /api/chats/<chat_id>
Delete a chat.

**Response:**
```json
{ "success": true }
```

---

### GET /api/mcp-status
Check documentation search connection status.

**Response:**
```json
{ "available": true, "pages": 113, "provider": "RealXmarket Docs" }
// or
{ "available": false, "reason": "Index not loaded" }
```

---

### POST /api/web-search
Search RealXmarket documentation directly.

**Request:**
```json
{ "query": "How to complete KYC" }
```

**Response:**
```json
{
  "query": "How to complete KYC",
  "results": "From RealXmarket documentation:\n\n### KYC Verification\nSource: https://doc-hub.xcavate.io/...\n\n[Documentation content...]"
}
```

---

## Frontend Modules

### js/config.js
```javascript
export const DEFAULT_MODEL = "gpt-4o";
export const MAX_CONTEXT_WINDOW = 8192;
```

---

### js/api.js
```javascript
// Stream agent response
async function streamAgentResponse(
  history: Array<{role: string, content: string}>,
  model: string,
  onChunk: (message: {content: string}) => void,
  onDone: () => void,
  signal: AbortSignal
): Promise<void>
```

---

### js/state.js
```javascript
// State getters/setters
getCurrentModel(): string
setCurrentModel(modelName: string): void
getActiveChatId(): string | null
setActiveChat(chatId: string, chatData: object): void
pushToHistory(turn: {role: string, content: string}): void
getAttachments(): Array<{name: string, content: string}>
addAttachment(file: {name: string, content: string}): void
removeAttachment(fileName: string): void
```

---

### js/ui.js
```javascript
// DOM elements export
export const dom = {
  form: HTMLFormElement,
  promptInput: HTMLTextAreaElement,
  sendButton: HTMLButtonElement,
  chatLog: HTMLDivElement,
  // ... more elements
}

// Key functions
addMessageToLog(role: 'user' | 'assistant', content: string, responseTime?: number): HTMLElement
renderInlineQuickReplies(anchorElement: HTMLElement, replies: string[], onSelect: (text: string) => void): void
bindQuickStartActions(onSelect: (prompt: string) => void): void
showLanding(): void
showChat(): void
updateTokenCounter(count: number, max: number): void
toggleLoading(isLoading: boolean): void
```

---

### js/app.js
```javascript
// Main entry point - runs on DOMContentLoaded
// Initializes event listeners, sets up UI

// Key functions (internal)
handleFormSubmit(event: Event): Promise<void>
submitQuickAction(promptText: string): Promise<void>
generateQuickReplies(lastUserPrompt: string, lastAssistantResponse: string): string[]
```

---

## Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | MISSING_CHAT_ID | Chat ID required for save operation |
| 404 | CHAT_NOT_FOUND | Specified chat ID does not exist |
| 500 | INTERNAL_ERROR | Server-side error occurred |

---

## Rate Limits

Currently no rate limiting is implemented. For production use, consider adding:
- Request throttling per IP
- Maximum requests per minute
- Context window size limits
