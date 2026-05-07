# server.py - Flask backend with LangGraph agent (OpenAI)
import os
import json
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import RealXmarket Docs client
try:
    from realxmarket_docs import initialize_docs, search_and_answer, get_docs_status
except ImportError:
    logger.warning("RealXmarket docs client not available")
    def initialize_docs(): return {"available": False}
    def search_and_answer(q): return ""
    def get_docs_status(): return {"available": False}

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

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/mcp-status', methods=['GET'])
def mcp_status():
    return jsonify(get_docs_status())

@app.route('/api/web-search', methods=['POST'])
def web_search():
    data = request.json
    query = data.get('query', '')
    results = search_and_answer(query)
    return jsonify({"query": query, "results": results})

@app.route('/api/chat', methods=['POST'])
def chat_stream():
    data = request.json
    messages = data.get('messages', [])
    model = data.get('model', 'gpt-4o')

    def generate():
        try:
            from langgraph_agent import stream_agent_response

            for event in stream_agent_response(messages, model):
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
                    chats.append({'id': data.get('id', chat_id), 'title': data.get('title', 'Untitled chat')})
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

    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True, "id": chat_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"success": True})
    return jsonify({"error": "Chat not found"}), 404

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

    print(f"Starting Flask server on http://localhost:{port}")

    try:
        result = initialize_docs()
        if result.get("available"):
            print(f"RealXmarket docs enabled: {result['pages']} pages indexed")
        else:
            print(f"RealXmarket docs disabled: {result.get('reason', 'Unknown error')}")
    except Exception as e:
        print(f"Docs init error: {e}")

    app.run(host='127.0.0.1', port=port)
