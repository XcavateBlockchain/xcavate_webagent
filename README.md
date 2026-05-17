<p align="center">
    <img src="ollapy-icon.png" alt="RealXmarket Web Assistant Logo" width="180" />
</p>

<h1 align="center">RealXmarket Web Assistant<br>AI Customer Support with Documentation Search</h1>

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/) [![Flask](https://img.shields.io/badge/Flask-3.x-black.svg)](https://flask.palletsprojects.com/) [![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

RealXmarket Web Assistant is a customer support chat interface for RealXmarket, built with a Flask backend and vanilla JavaScript frontend. The AI uses OpenAI's GPT-4o and automatically searches the official RealXmarket documentation to provide accurate, up-to-date answers.

## 📖 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Server](#running-the-server)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

---

## ✨ Features

*   **🤖 AI-Powered Support:** Uses OpenAI GPT-4o to understand and respond to user queries
*   **📚 Automatic Documentation Search:** AI automatically searches RealXmarket documentation when needed
*   **💬 Real-Time Streaming:** Responses stream token-by-token for interactive conversations
*   **💾 Chat History:** All conversations are automatically saved as JSON files
*   **🔍 Built-in Search:** Direct web search endpoint for documentation queries
*   **✍️ Markdown Rendering:** Beautifully formatted AI responses with code blocks, tables, and lists
*   **🛡️ Security:** Client-side HTML sanitization using DOMPurify
*   **📱 Responsive Design:** Works on desktop and mobile browsers
*   **🔄 Quick Actions:** Pre-defined buttons for common support topics
*   **💡 Smart Follow-ups:** AI suggests follow-up questions after each response

---

## 🖼️ Screenshots

<p align="center">
    <img src="screenshot.png" alt="RealXmarket Web Assistant Screenshot" width="80%" />
</p>

---

## 🛠️ Architecture

The application consists of a Python Flask backend and a vanilla JavaScript frontend:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser       │────▶│   Flask Server   │────▶│   OpenAI API    │
│   (index.html)  │◀────│   (server.py)    │◀────│   (gpt-4o)      │
│                 │     │                  │     │                 │
│   js/app.js     │     │ langgraph_agent  │────▶│ realxmarket     │
│   js/api.js     │     │                  │     │ docs (tool)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Key Components:**

1.  **`server.py`** - Flask backend serving static files and REST API endpoints
2.  **`langgraph_agent.py`** - Agent logic with tool integration for documentation search
3.  **`realxmarket_docs.py`** - Documentation search client (indexes doc-hub.xcavate.io)
4.  **`js/*.js`** - Frontend modules (app, api, state, ui, config)

---

## 🚀 Getting Started

### Prerequisites

*   Python 3.10+ and `pip`
*   OpenAI API key with access to GPT-4o

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/xcavate-web-assistant.git
    cd xcavate-web-assistant
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Running the Server

1.  **Set your OpenAI API key:**

    ```bash
    export OPENAI_API_KEY="sk-your-api-key-here"
    ```

2.  **Start the server:**

    ```bash
    python server.py [port]  # defaults to port 8001
    ```

3.  **Open in browser:**

    Navigate to `http://localhost:8001`

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |

### Default Settings

Edit `js/config.js` to customize:

```javascript
// js/config.js
export const DEFAULT_MODEL = "gpt-4o";
export const MAX_CONTEXT_WINDOW = 8192;
```

---

## 🤓 API Endpoints

### Chat & Conversation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Stream AI response (NDJSON) |
| `GET` | `/api/chats` | List all saved chats |
| `POST` | `/api/chats` | Save or update a chat |
| `GET` | `/api/chats/<id>` | Get a specific chat |
| `DELETE` | `/api/chats/<id>` | Delete a chat |

### Documentation Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/mcp-status` | Check docs connection status |
| `POST` | `/api/web-search` | Search documentation directly |

See [`docs/api-reference.md`](docs/api-reference.md) for detailed request/response formats.

---

## 🧪 Testing

Run the unit test suite:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_realxmarket_docs.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage:**

-   `tests/test_realxmarket_docs.py` - Documentation search module (25 tests)
-   `tests/test_server.py` - Flask API endpoints (17 tests)
-   `tests/test_langgraph_agent.py` - Agent logic and tools (12 tests)

---

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [`docs/project-overview.md`](docs/project-overview.md) | High-level project overview and tech stack |
| [`docs/architecture.md`](docs/architecture.md) | Detailed architecture and message flows |
| [`docs/api-reference.md`](docs/api-reference.md) | Complete API endpoint reference |
| [`docs/components.md`](docs/components.md) | UI components and data models |
| [`docs/development-guide.md`](docs/development-guide.md) | Guide for adding features |
| [`docs/system-prompt.md`](docs/system-prompt.md) | System prompt reference and customization |

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for improvements:

1.  Fork the repository
2.  Create a feature branch
3.  Make your changes
4.  Submit a pull request

**Areas for contribution:**

-   Adding new AI tools/capabilities
-   Enhancing the UI/UX
-   Improving documentation search accuracy
-   Adding chat export functionality (Markdown/PDF)
-   Implementing dark mode themes

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🔗 Links

-   **RealXmarket Docs:** https://doc-hub.xcavate.io
-   **Issue Tracker:** https://github.com/your-username/xcavate-web-assistant/issues
-   **OpenAI:** https://platform.openai.com
