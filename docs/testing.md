# Testing Guide

## Overview

This project uses `pytest` for unit testing. The test suite covers:

-   Backend API endpoints (Flask)
-   Agent logic and tool integration (LangGraph)
-   Documentation search functionality

## Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Install pytest if needed
pip install pytest

# Run all tests
pytest tests/ -v

# Run with color output
pytest tests/ -v --color=yes

# Run specific test file
pytest tests/test_realxmarket_docs.py -v

# Run specific test function
pytest tests/test_server.py::TestWebSearchEndpoint::test_search_with_query -v

# Run tests matching pattern
pytest tests/ -k "search" -v

# Run with coverage report
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

## Test Structure

### test_realxmarket_docs.py

Tests for the documentation search module (`realxmarket_docs.py`).

**Coverage:**
- URL/title extraction functions
- Keyword extraction and filtering
- Content cleaning and normalization
- Documentation search algorithm
- Page fetching and content limits
- Docs status reporting
- Sitemap initialization

**Key Tests:**
```python
def test_keyword_matching():
    # Verify search returns relevant pages

def test_support_query_boosts_tester_guide():
    # Verify support queries prioritize tester guides

def test_successful_initialization():
    # Verify sitemap parsing works correctly
```

### test_server.py

Tests for the Flask backend (`server.py`).

**Coverage:**
- Static file routes (CSS, JS)
- MCP status endpoint
- Web search endpoint
- Chat CRUD operations
- Error handling

**Key Tests:**
```python
def test_index_returns_html():
    # Verify homepage serves index.html

def test_search_with_query():
    # Verify web search processes queries

def test_save_chat():
    # Verify chat persistence to disk

def test_delete_chat_found():
    # Verify chat deletion works
```

### test_langgraph_agent.py

Tests for the LangGraph agent (`langgraph_agent.py`).

**Coverage:**
- System prompt validation
- Agent state structure
- Tool definition and invocation
- LLM creation with tools
- Workflow graph creation
- Streaming response handling

**Key Tests:**
```python
def test_system_prompt_contains_guidelines():
    # Verify system prompt has required sections

def test_tool_invokes_search():
    # Verify tool calls search function

def test_creates_workflow():
    # Verify agent graph compiles correctly
```

## Test Fixtures

### conftest.py

Shared fixtures for all tests:

```python
# Environment setup
@pytest.fixture(autouse=True)
def setup_env():
    """Sets OPENAI_API_KEY=test-key"""

# Mock requests module
@pytest.fixture
def mock_requests():
    """Mock requests for docs tests"""

# Sample data
@pytest.fixture
def sample_sitemap_xml():
    """Sample sitemap for initialization tests"""

@pytest.fixture
def mock_logs_dir(tmp_path):
    """Temporary logs directory for server tests"""
```

## Writing New Tests

### Best Practices

1. **Use descriptive names:**
   ```python
   def test_search_returns_empty_when_not_initialized():
       # Clear what is being tested
   ```

2. **Arrange-Act-Assert pattern:**
   ```python
   def test_example():
       # Arrange
       state = {"initialized": False}

       # Act
       result = search_docs("query", state)

       # Assert
       assert result == []
   ```

3. **Use fixtures for setup:**
   ```python
   def test_with_fixture(mock_logs_dir, client):
       # Reuse common setup
   ```

4. **Mock external dependencies:**
   ```python
   @patch('realxmarket_docs.requests.get')
   def test_api_call(mock_get):
       mock_get.return_value = MagicMock(status_code=200)
   ```

### Adding a New Test File

```python
# tests/test_new_feature.py
import pytest
from unittest.mock import patch, MagicMock

class TestNewFeature:
    """Tests for new feature"""

    def test_basic_behavior(self):
        # Test happy path
        pass

    def test_error_handling(self):
        # Test edge cases
        pass

    @patch('module.external_call')
    def test_with_mock(self, mock_call):
        # Test with mocked dependencies
        pass
```

## Coverage Goals

Aim for:
-   **80%+ line coverage** on core modules
-   **100% coverage** on utility functions
-   **All critical paths** tested

Generate coverage report:
```bash
pytest tests/ --cov=server --cov=langgraph_agent --cov=realxmarket_docs --cov-report=term-missing
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest tests/ --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests failing due to API calls
Make sure you're mocking external calls properly:
```python
@patch('module.requests.get')  # Patch where it's used, not where it's defined
```

### Import errors
Check that mocks are set up before imports happen:
```python
# In conftest.py or at top of test file
sys.modules['external_dep'] = MagicMock()
```

### Fixture not found
Ensure `conftest.py` is in the same directory or parent directory.
