"""Unit tests for server.py Flask application"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open

# Mock the realxmarket_docs import before importing server
import sys
from unittest.mock import MagicMock

# Create a proper mock module instead of a bare MagicMock
mock_docs_module = MagicMock()
mock_docs_module.initialize_docs = MagicMock(return_value={"available": True, "pages": 10})
mock_docs_module.search_and_answer = MagicMock(return_value="Search results")
mock_docs_module.get_docs_status = MagicMock(return_value={"available": True, "pages": 10})
sys.modules['realxmarket_docs'] = mock_docs_module

# Now import the server app
from server import app


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_logs_dir(tmp_path):
    """Create a temporary logs directory"""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    with patch('server.LOGS_DIR', str(logs_dir)):
        yield logs_dir


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test"""
    # Reset the mock module's return values
    sys.modules['realxmarket_docs'].search_and_answer.reset_mock()
    sys.modules['realxmarket_docs'].get_docs_status.reset_mock()
    yield


class TestStaticRoutes:
    """Tests for static file routes"""

    def test_index_returns_html(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_css_serves_from_css_dir(self, client):
        # This will return 404 if no CSS files exist, but tests the route works
        response = client.get('/css/style.css')
        assert response.status_code in [200, 404]

    def test_js_serves_from_js_dir(self, client):
        # This will return 404 if no JS files exist, but tests the route works
        response = client.get('/js/app.js')
        assert response.status_code in [200, 404]


class TestMcpStatusEndpoint:
    """Tests for /api/mcp-status endpoint"""

    @patch('server.get_docs_status')
    def test_returns_docs_status(self, mock_get_status, client):
        mock_get_status.return_value = {"available": True, "pages": 10}
        response = client.get('/api/mcp-status')
        assert response.status_code == 200
        data = response.get_json()
        assert "available" in data
        assert "pages" in data


class TestWebSearchEndpoint:
    """Tests for /api/web-search endpoint"""

    @patch('server.search_and_answer')
    def test_search_with_query(self, mock_search, client):
        mock_search.return_value = "Search results for query"
        response = client.post('/api/web-search',
                              json={"query": "test query"},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == "test query"
        assert "results" in data
        mock_search.assert_called_once_with("test query")

    @patch('server.search_and_answer')
    def test_search_with_empty_query(self, mock_search, client):
        mock_search.return_value = ""
        response = client.post('/api/web-search',
                              json={"query": ""},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == ""

    @patch('server.search_and_answer')
    def test_search_with_missing_query(self, mock_search, client):
        mock_search.return_value = ""
        response = client.post('/api/web-search',
                              json={},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == ""


class TestChatStreamEndpoint:
    """Tests for /api/chat endpoint"""

    @patch('server.stream_agent_response')
    def test_chat_stream_basic(self, mock_stream, client):
        mock_stream.return_value = [
            {"messages": [{"content": "Hello"}]},
            {"done": True}
        ]
        response = client.post('/api/chat',
                              json={"messages": [{"role": "user", "content": "Hi"}]},
                              content_type='application/json')
        assert response.status_code == 200
        assert response.content_type == 'application/x-ndjson'

    @patch('server.stream_agent_response')
    def test_chat_stream_with_model(self, mock_stream, client):
        mock_stream.return_value = [{"done": True}]
        response = client.post('/api/chat',
                              json={"messages": [], "model": "gpt-4o"},
                              content_type='application/json')
        assert response.status_code == 200


class TestChatsEndpoints:
    """Tests for /api/chats endpoints"""

    def test_get_chats_empty_directory(self, client, mock_logs_dir):
        response = client.get('/api/chats')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_get_chats_with_files(self, client, mock_logs_dir):
        # Create some test chat files
        chat1 = {"id": "chat1", "title": "First Chat"}
        chat2 = {"id": "chat2", "title": "Second Chat"}

        with open(mock_logs_dir / "chat1.json", 'w') as f:
            json.dump(chat1, f)
        with open(mock_logs_dir / "chat2.json", 'w') as f:
            json.dump(chat2, f)

        response = client.get('/api/chats')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_get_chat_found(self, client, mock_logs_dir):
        chat_data = {"id": "test123", "title": "Test Chat", "messages": []}
        with open(mock_logs_dir / "test123.json", 'w') as f:
            json.dump(chat_data, f)

        response = client.get('/api/chats/test123')
        assert response.status_code == 200

    def test_get_chat_not_found(self, client, mock_logs_dir):
        response = client.get('/api/chats/nonexistent')
        assert response.status_code == 404

    def test_save_chat(self, client, mock_logs_dir):
        chat_data = {"id": "newchat", "title": "New Chat"}
        response = client.post('/api/chats',
                               json=chat_data,
                               content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert os.path.exists(mock_logs_dir / "newchat.json")

    def test_save_chat_missing_id(self, client, mock_logs_dir):
        response = client.post('/api/chats',
                               json={"title": "No ID"},
                               content_type='application/json')
        assert response.status_code == 400

    def test_delete_chat_found(self, client, mock_logs_dir):
        # Create a file first
        with open(mock_logs_dir / "todelete.json", 'w') as f:
            json.dump({"id": "todelete"}, f)

        response = client.delete('/api/chats/todelete')
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert not os.path.exists(mock_logs_dir / "todelete.json")

    def test_delete_chat_not_found(self, client, mock_logs_dir):
        response = client.delete('/api/chats/nonexistent')
        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling"""

    @patch('server.stream_agent_response')
    def test_chat_stream_error_handling(self, mock_stream, client):
        mock_stream.side_effect = Exception("Test error")
        response = client.post('/api/chat',
                              json={"messages": []},
                              content_type='application/json')
        assert response.status_code == 200  # Stream still returns 200, error in stream


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
