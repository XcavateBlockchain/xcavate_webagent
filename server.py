# server.py - Flask backend with LangGraph agent (OpenAI)
import os
import json
import sys
import logging
import re
import fcntl
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask import Response
from dotenv import load_dotenv


load_dotenv(override=False)


def get_openai_model() -> str:
    return os.environ.get("OPENAI_MODEL")


def get_env_int(name: str):
    raw_value = os.environ.get(name)
    if raw_value is None:
        raise ValueError(f"{name} environment variable not set")

    cleaned_value = raw_value.strip().strip('"\'').rstrip(';')
    match = re.match(r"^\d+", cleaned_value)
    if not match:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}")

    return int(match.group(0))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import GitBook MCP client
try:
    from gitbook_mcp_client import get_mcp_status, search_documentation
except ImportError:
    logger.warning("GitBook MCP client not available")
    def get_mcp_status(): return {"available": False}
    def search_documentation(q): return ""


def get_docs_status():
    """Return GitBook MCP status (primary docs source)."""
    return get_mcp_status()


app = Flask(__name__)


@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.root_path, 'css'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'js'), filename)


LOGS_DIR = 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

TICKETS_DIR = 'tickets'
TICKETS_FILE = os.path.join(TICKETS_DIR, 'tickets.json')
if not os.path.exists(TICKETS_DIR):
    os.makedirs(TICKETS_DIR)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/mcp-status', methods=['GET'])
def mcp_status():
    return jsonify(get_docs_status())


@app.route('/api/config', methods=['GET'])
def runtime_config():
    return jsonify({
        "default_model": get_openai_model(),
        "max_context_window": get_env_int("MAX_CONTEXT_WINDOW")
    })


@app.route('/api/web-search', methods=['POST'])
def web_search():
    data = request.json
    query = data.get('query', '')
    results = search_documentation(query)
    return jsonify({"query": query, "results": results})


@app.route('/api/chat', methods=['POST'])
def chat_stream():
    data = request.json
    messages = data.get('messages', [])

    def generate():
        try:
            from langgraph_agent import stream_agent_response

            for event in stream_agent_response(messages):
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    if hasattr(last_msg, 'content'):
                        content = last_msg.content
                    elif isinstance(last_msg, dict):
                        content = last_msg.get("content", "")
                    else:
                        content = ""

                    if content:
                        chunk = {"message": {"content": content}, "done": False}
                        yield json.dumps(chunk) + "\n"

            yield json.dumps({"done": True}) + "\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield json.dumps({"error": str(e), "done": True}) + "\n"

    return Response(generate(), mimetype='application/x-ndjson')


@app.route('/api/chats', methods=['GET'])
def get_chats():
    chats = []
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.json'):
            chat_id = filename.split('.')[0]
            try:
                with open(os.path.join(LOGS_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    chats.append({
                        'id': data.get('id', chat_id),
                        'title': data.get('title', 'Untitled chat'),
                        'model': data.get('model'),
                        'datetime': data.get('datetime')
                    })
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error reading file {filename}: {e}")
    chats.sort(key=lambda x: str(x['id']), reverse=True)
    return jsonify(chats)


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        return send_from_directory(LOGS_DIR, f"{chat_id}.json")
    return jsonify({"error": "Chat not found"}), 404


@app.route('/api/chats', methods=['POST'])
def save_chat():
    chat_data = request.json
    chat_id = chat_data.get('id')
    if not chat_id:
        return jsonify({"error": "Missing chat ID"}), 400

    # Add wallet info if provided
    if 'walletAddress' in chat_data or 'hasWallet' in chat_data:
        chat_data['walletAddress'] = chat_data.get('walletAddress', None)
        chat_data['hasWallet'] = chat_data.get('hasWallet', False)

    # Add datetime timestamp
    chat_data['datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    lock_file = filepath + '.lock'

    try:
        # Use file locking for concurrent access safety
        with open(lock_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                with open(filepath, 'w', encoding='utf-8') as tf:
                    json.dump(chat_data, tf, indent=2, ensure_ascii=False)
                return jsonify({"success": True, "id": chat_id})
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"success": True})
    return jsonify({"error": "Chat not found"}), 404


@app.route('/api/wallet/log', methods=['POST'])
def log_wallet_event():
    data = request.json
    address = data.get('address')
    event_type = data.get('event_type', 'connected')

    if not address:
        return jsonify({"error": "Missing address"}), 400

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "wallet_address": address
    }

    log_file = os.path.join(LOGS_DIR, "wallet_events.json")
    try:
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        logs.append(log_entry)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        logger.info(f"Wallet event logged: {event_type} for address {address[:8]}...")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error writing wallet log: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.json

    # Validate required fields
    required_fields = ['ticket_id', 'wallet_address', 'title', 'category', 'priority', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Create ticket entry
    ticket = {
        "ticket_id": data['ticket_id'],
        "wallet_address": data['wallet_address'],
        "title": data['title'],
        "category": data['category'],
        "priority": data['priority'],
        "description": data['description'],
        "status": "open",
        "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    try:
        # Use file locking to prevent race conditions with concurrent users
        lock_file = TICKETS_FILE + '.lock'

        # Create lock file if it doesn't exist
        with open(lock_file, 'w') as f:
            # Acquire exclusive lock (blocks until available)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

            try:
                # Load existing tickets
                tickets = []
                if os.path.exists(TICKETS_FILE):
                    with open(TICKETS_FILE, 'r', encoding='utf-8') as tf:
                        tickets = json.load(tf)

                # Add new ticket
                tickets.append(ticket)

                # Save back to file
                with open(TICKETS_FILE, 'w', encoding='utf-8') as tf:
                    json.dump(tickets, tf, indent=2, ensure_ascii=False)

                logger.info(f"Ticket created: {data['ticket_id']} for wallet {data['wallet_address'][:8]}...")
                return jsonify({"success": True, "ticket_id": data['ticket_id']})
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    print(f"Starting Flask server on http://0.0.0.0:{port}")

    # Check GitBook MCP connection status
    try:
        status = get_docs_status()
        if status.get("available"):
            tools = status.get("tools", [])
            print(f"GitBook MCP connected: {len(tools)} tools available ({', '.join(tools)})")
        else:
            print(f"GitBook MCP unavailable: {status.get('reason', 'Unknown error')}")
    except Exception as e:
        print(f"Docs status error: {e}")

    # Bind to 0.0.0.0 for container environments (EC2, Docker, etc.)
    app.run(host='0.0.0.0', port=port)
