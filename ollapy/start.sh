#!/bin/bash

# --- Configuration ---
SERVER_FILE="server.py"
PORT=8000
URL="http://localhost:$PORT"

# --- Cleanup function ---
cleanup() {
  echo -e "\n\n SIGINT received. Shutting down servers..."
    kill $server_pid
    kill $ollama_pid
  echo "Servers stopped. Exiting."
    exit
}
trap cleanup INT

# --- Pre-checks ---
if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 not found."
    exit 1
fi

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

if [ ! -f "$SERVER_FILE" ]; then
  echo "Error: File '$SERVER_FILE' not found. Make sure it is in this folder."
    exit 1
fi

if ! command -v ollama &> /dev/null; then
  echo "Error: ollama not found. Make sure it is installed and in your PATH."
    exit 1
fi

# --- Check whether Ollama is already running ---
if pgrep -f "ollama serve" > /dev/null; then
  echo "Ollama is already running."
else
  echo "1. Starting Ollama server in the background..."
    OLLAMA_ORIGINS="*" ollama serve &
    ollama_pid=$!
    echo "  - Ollama PID: $ollama_pid"
  sleep 3 # Give Ollama time to start
fi

# --- Start servers ---
echo "2. Starting Flask web server (serves UI and manages logs) on port $PORT..."
python3 $SERVER_FILE $PORT &
server_pid=$!

echo -e "\nServers started successfully:"
echo "  - Ollama PID: $ollama_pid"
echo "  - Web Server PID: $server_pid"
echo "  - Web interface: $URL"

sleep 2

# --- Open browser ---
echo -e "\n3. Opening chat in browser..."
if command -v xdg-open &> /dev/null; then
  xdg-open "$URL"
elif command -v open &> /dev/null; then
  open "$URL"
else
  echo "Could not open browser. Open it manually at: $URL"
fi

echo -e "\n--- Chat is ready! ---"
echo "Press Ctrl+C in this terminal window to stop everything."

wait
