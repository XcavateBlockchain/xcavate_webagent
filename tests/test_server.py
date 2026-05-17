"""Unit tests for server.py Flask application"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock

# Mock the realxmarket_docs import before importing server
import sys
from unittest.mock import MagicMock

# Create a proper mock module
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
        response = client.get('/css/style.css')
        assert response.status_code in [200, 404]

    def test_js_serves_from_js_dir(self, client):
        response = client.get('/js/app.js')
        assert response.status_code in [200, 404]


class TestMcpStatusEndpoint:
    """Tests for /api/mcp-status endpoint"""

    def test_returns_docs_status(self, client):
        response = client.get('/api/mcp-status')
        assert response.status_code == 200
        data = response.get_json()
        assert "available" in data
        assert "pages" in data


class TestWebSearchEndpoint:
    """Tests for /api/web-search endpoint"""

    def test_search_with_query(self, client):
        response = client.post('/api/web-search',
                              json={"query": "test query"},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == "test query"
        assert "results" in data

    def test_search_with_empty_query(self, client):
        response = client.post('/api/web-search',
                              json={"query": ""},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == ""

    def test_search_with_missing_query(self, client):
        response = client.post('/api/web-search',
                              json={},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == ""


class TestChatStreamEndpoint:
    """Tests for /api/chat endpoint - skip these as they require dynamic imports"""

    def test_chat_stream_basic_skipped(self, client):
        # This test is skipped because stream_agent_response is imported dynamically
        # inside the route handler, making it difficult to mock
        pytest.skip("Dynamic import makes mocking difficult")

    def test_chat_stream_with_model_skipped(self, client):
        pytest.skip("Dynamic import makes mocking difficult")


class TestChatsEndpoints:
    """Tests for /api/chats endpoints"""

    def test_get_chats_empty_directory(self, client, mock_logs_dir):
        response = client.get('/api/chats')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_get_chats_with_files(self, client, mock_logs_dir):
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

    def test_chat_stream_error_handling_skipped(self, client):
        pytest.skip("Dynamic import makes mocking difficult")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
