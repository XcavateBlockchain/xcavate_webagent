# Component Reference

## UI Components

### Landing Page
Displayed when user first loads the app. Contains:
- **Header** - Title and "Message" button
- **Search bar** - Quick question input
- **Self Service section** - Pre-defined support cards
- **Category columns** - Organized help topics
- **FAQ section** - Common questions

### Chat View
Main chat interface:
- **Header** - Back button, title, MCP status indicator, new chat button
- **Welcome state** - Shown when chat is empty with quick actions
- **Chat log** - Message history area
- **Attachment area** - File attachments display
- **Input area** - Textarea + send button + token counter

### Sidebar
Collapsible history panel:
- List of saved chats
- Each chat shows title and model tag
- Delete button per chat
- Click to load chat

### Messages
Two types:
- **User message** - Right-aligned, plain text
- **Assistant message** - Left-aligned, rendered Markdown with cursor animation

### Quick Action Buttons
Three locations:
1. Landing page self-service cards
2. Chat view welcome state grid
3. Inline after AI responses (follow-up suggestions)

---

## Data Models

### Chat Object
```javascript
{
  id: string,           // Unique identifier (timestamp)
  title: string,        // First prompt or custom title
  history: [
    {
      role: "user" | "assistant",
      content: string,
      responseTime?: number  // Only for assistant messages
    }
  ],
  model: string         // Model used (e.g., "gpt-4o")
}
```

### Message Object (API)
```javascript
{
  role: "system" | "user" | "assistant" | "tool",
  content: string
}
```

### Attachment Object
```javascript
{
  name: string,   // Filename
  content: string // File contents (text only)
}
```

---

## CSS Classes

### Layout
- `.app-layout` - Main container
- `.sidebar-controls` - Collapsible sidebar
- `.chat-container` - Chat view wrapper

### Messages
- `.message` - Base message class
- `.user-message` - User message styling
- `.assistant-message` - Assistant message styling
- `.cursor` - Typing cursor animation

### Quick Actions
- `.quick-action-btn` - Quick reply button
- `.quick-reply-btn` - Inline follow-up buttons
- `.inline-quick-replies` - Container for inline buttons

### Status Indicators
- `.mcp-status-indicator` - Docs connection status
- `.mcp-connected` - Green indicator
- `.mcp-disconnected` - Gray indicator

---

## Event Flow

### User Types and Submits
1. `keydown` on textarea → Enter submits (Shift+Enter inserts newline)
2. `submit` on form → `handleFormSubmit()`
3. Show loading state, clear input
4. Call `api.streamAgentResponse()`
5. Render user message immediately
6. Stream AI response token-by-token
7. On done: add response time, show quick replies, save chat

### User Clicks Quick Action
1. `click` on button → `submitQuickAction(promptText)`
2. Set input value to prompt text
3. Submit form programmatically
4. Same flow as normal submit

### User Loads Old Chat
1. `click` on chat in sidebar → `loadChat(chatId)`
2. Fetch chat data from `/api/chats/<id>`
3. Set model, restore history
4. Render all messages
5. Update token count

### User Deletes Chat
1. `click` on delete button → `deleteChat(chatId)`
2. Confirm dialog
3. DELETE request to `/api/chats/<id>`
4. Remove from UI, reload list
