import os
import json
import sys
from flask import Flask, request, jsonify, send_from_directory # type: ignore
from flask import Response # type: ignore

# Initialize Flask application
app = Flask(__name__)

# Add routes for static assets
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.root_path, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'js'), filename)

# Create logs directory if it does not exist
LOGS_DIR = 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# API: Serve main chat file
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/favicon.ico')
def favicon():
    # A simple chat bubble SVG icon
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <path d="M10 10 H 90 V 70 H 30 L 10 90 V 70 H 10 Z" 
        fill="#4a90e2" stroke="#e0e0e0" stroke-width="5"/>
    </svg>"""
    return Response(svg_icon, mimetype='image/svg+xml')

# API: Get the list of all chats
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
                        'title': data.get('title', 'Untitled chat')
                    })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error reading file {filename}: {e}")
    # Sort by ID (timestamp) from newest to oldest
    chats.sort(key=lambda x: str(x['id']), reverse=True)
    return jsonify(chats)

# API: Get content of a specific chat
@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        return send_from_directory(LOGS_DIR, f"{chat_id}.json")
    return jsonify({"error": "Chat not found"}), 404

# API: Save (create or update) a chat
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

# API: Delete a chat
@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    filepath = os.path.join(LOGS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"success": True})
    return jsonify({"error": "Chat not found"}), 404

# Start server
if __name__ == '__main__':
    # Read port from command line, default to 8001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    
    print(f"Starting Flask server on http://localhost:{port}")
    print("This server hosts the interface and saves/loads chats.")
    app.run(host='127.0.0.1', port=port)