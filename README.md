# xcavate Web Agent

This repository contains a local AI help center web app designed to provide customer-support style answers through an Ollama-backed local model.

## Project Overview

The main application lives in `ai-help-center/` and includes:

- A static frontend (`public/`) with a chat-style support interface
- A lightweight Python HTTP server (`server.py`)
- A local API proxy endpoint (`POST /api/ask`) that forwards prompts to Ollama

## Features

- Local-first setup (no cloud API required)
- Simple one-command Python server startup
- Built-in preset support prompts in the UI
- Health check endpoint (`GET /health`)
- Configurable model, server port, and Ollama endpoint via environment variables

## Requirements

- Python 3.8+
- Ollama installed and running locally
- At least one Ollama model pulled (for example, `llama3`)

## Quick Start

1. Move into the app directory:

```bash
cd ai-help-center
```

2. Start Ollama and pull a model if needed:

```bash
ollama pull llama3
```

3. Start the server:

```bash
python3 server.py
```

4. Open the app in your browser:

```text
http://127.0.0.1:3000
```

## Configuration

You can configure runtime behavior with environment variables:

- `PORT` (default: `3000`)
- `OLLAMA_URL` (default: `http://localhost:11434/api/generate`)
- `OLLAMA_MODEL` (default: `llama3`)

Example:

```bash
OLLAMA_MODEL=mistral PORT=8080 python3 server.py
```

## API Endpoints

- `POST /api/ask`: Sends `{ "prompt": "..." }` to local Ollama and returns an AI response
- `GET /health`: Returns service status and active model

## Repository Structure

```text
xcavate_webagent/
├── README.md
├── LICENSE
└── ai-help-center/
	├── README.md
	├── server.py
	└── public/
		├── index.html
		├── styles.css
		└── app.js
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.