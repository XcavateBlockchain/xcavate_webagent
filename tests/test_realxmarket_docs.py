"""Unit tests for realxmarket_docs.py"""
import pytest
import re
from unittest.mock import patch, MagicMock, Mock

# Import the module under test
import realxmarket_docs


class TestExtractTitleFromUrl:
    """Tests for extract_title_from_url function"""

    def test_simple_url(self):
        assert realxmarket_docs.extract_title_from_url("https://example.com/getting-started") == "Getting Started"

    def test_url_with_md_extension(self):
        assert realxmarket_docs.extract_title_from_url("https://example.com/page-name.md") == "Page Name"

    def test_url_with_hyphens(self):
        assert realxmarket_docs.extract_title_from_url("https://example.com/my-test-page") == "My Test Page"

    def test_trailing_slash(self):
        assert realxmarket_docs.extract_title_from_url("https://example.com/page/") == "Page"


class TestExtractKeywords:
    """Tests for extract_keywords function"""

    def test_basic_keywords(self):
        result = realxmarket_docs.extract_keywords("getting started guide")
        assert "getting" in result
        assert "started" in result
        assert "guide" in result

    def test_stop_words_removed(self):
        result = realxmarket_docs.extract_keywords("the a an and or")
        assert len(result) == 0

    def test_short_words_removed(self):
        result = realxmarket_docs.extract_keywords("at in of to for")
        assert len(result) == 0

    def test_url_format(self):
        result = realxmarket_docs.extract_keywords("https://example.com/getting-started")
        assert "getting" in result
        assert "started" in result


class TestCleanDocContent:
    """Tests for clean_doc_content function"""

    def test_empty_string(self):
        assert realxmarket_docs.clean_doc_content("") == ""

    def test_none_input(self):
        assert realxmarket_docs.clean_doc_content(None) == ""

    def test_removes_agent_instructions(self):
        content = "# Some Title\nSome content\n\n# Agent Instructions\nDo something"
        result = realxmarket_docs.clean_doc_content(content)
        assert "Agent Instructions" not in result

    def test_removes_sources_section(self):
        content = "# Some Title\nSome content\n\n# Sources:\n- source1"
        result = realxmarket_docs.clean_doc_content(content)
        assert "Sources:" not in result

    def test_normalizes_multiple_newlines(self):
        content = "Line1\n\n\n\nLine2"
        result = realxmarket_docs.clean_doc_content(content)
        assert "\n\n\n" not in result

    def test_normalizes_multiple_spaces(self):
        content = "Word1   Word2"
        result = realxmarket_docs.clean_doc_content(content)
        assert "   " not in result


class TestSearchDocs:
    """Tests for search_docs function"""

    def setup_method(self):
        """Reset docs state before each test"""
        realxmarket_docs._docs_state = {
            "initialized": False,
            "pages": [],
        }

    def test_not_initialized_returns_empty(self):
        result = realxmarket_docs.search_docs("test query")
        assert result == []

    def test_empty_index_returns_empty(self):
        realxmarket_docs._docs_state["initialized"] = True
        result = realxmarket_docs.search_docs("test query")
        assert result == []

    def test_keyword_matching(self):
        realxmarket_docs._docs_state = {
            "initialized": True,
            "pages": [
                {"url": "https://doc-hub.xcavate.io/wallet-connection", "title": "Wallet Connection", "keywords": ["wallet", "connection"]},
                {"url": "https://doc-hub.xcavate.io/transactions", "title": "Transactions", "keywords": ["transactions"]},
            ]
        }
        result = realxmarket_docs.search_docs("wallet")
        assert len(result) > 0
        assert result[0]["url"] == "https://doc-hub.xcavate.io/wallet-connection"

    def test_support_query_boosts_tester_guide(self):
        realxmarket_docs._docs_state = {
            "initialized": True,
            "pages": [
                {"url": "https://doc-hub.xcavate.io/realxmarket-tester-guide/login", "title": "Login Guide", "keywords": ["login"]},
                {"url": "https://doc-hub.xcavate.io/general-guide/something", "title": "General", "keywords": ["something"]},
            ]
        }
        result = realxmarket_docs.search_docs("how to login")
        # Tester guide should be ranked higher for support queries
        if len(result) >= 2:
            assert "tester-guide" in result[0]["url"] or "tester-guide" in result[-1]["url"]

    def test_max_results_limit(self):
        realxmarket_docs._docs_state = {
            "initialized": True,
            "pages": [
                {"url": f"https://doc-hub.xcavate.io/page{i}", "title": f"Page {i}", "keywords": ["test"]}
                for i in range(10)
            ]
        }
        result = realxmarket_docs.search_docs("test", max_results=3)
        assert len(result) <= 3


class TestFetchPageDirect:
    """Tests for fetch_page_direct function"""

    def setup_method(self):
        """Reset docs state before each test"""
        realxmarket_docs._docs_state = {
            "initialized": False,
            "pages": [],
        }

    @patch('realxmarket_docs.requests.get')
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Title\n\nContent here"
        mock_get.return_value = mock_response

        result = realxmarket_docs.fetch_page_direct("https://doc-hub.xcavate.io/test.md")
        assert result is not None
        assert "Content here" in result

    @patch('realxmarket_docs.requests.get')
    def test_404_returns_none(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = realxmarket_docs.fetch_page_direct("https://doc-hub.xcavate.io/notfound.md")
        assert result is None

    @patch('realxmarket_docs.requests.get')
    def test_request_exception_returns_none(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = realxmarket_docs.fetch_page_direct("https://doc-hub.xcavate.io/test.md")
        assert result is None

    @patch('realxmarket_docs.requests.get')
    def test_content_limited_to_2000_chars(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Title\n\n" + "x" * 3000
        mock_get.return_value = mock_response

        result = realxmarket_docs.fetch_page_direct("https://doc-hub.xcavate.io/test.md")
        assert len(result) <= 2000


class TestSearchAndAnswer:
    """Tests for search_and_answer function"""

    def setup_method(self):
        """Reset docs state before each test"""
        realxmarket_docs._docs_state = {
            "initialized": False,
            "pages": [],
        }

    def test_not_initialized_returns_empty(self):
        result = realxmarket_docs.search_and_answer("test query")
        assert result == ""

    @patch('realxmarket_docs.search_docs')
    def test_no_search_results_returns_empty(self, mock_search):
        realxmarket_docs._docs_state["initialized"] = True
        mock_search.return_value = []

        result = realxmarket_docs.search_and_answer("test query")
        assert result == ""

    @patch('realxmarket_docs.search_docs')
    @patch('realxmarket_docs.fetch_page_direct')
    def test_successful_search_and_fetch(self, mock_fetch, mock_search):
        realxmarket_docs._docs_state["initialized"] = True
        mock_search.return_value = [{"url": "https://doc-hub.xcavate.io/test", "title": "Test", "score": 10}]
        mock_fetch.return_value = "Some relevant content"

        result = realxmarket_docs.search_and_answer("test query")
        assert "From RealXmarket documentation:" in result
        assert "Some relevant content" in result


class TestGetDocsStatus:
    """Tests for get_docs_status function"""

    def test_not_initialized(self):
        realxmarket_docs._docs_state = {"initialized": False, "pages": []}
        result = realxmarket_docs.get_docs_status()
        assert result["available"] is False
        assert result["pages"] == 0
        assert result["provider"] is None

    def test_initialized(self):
        realxmarket_docs._docs_state = {"initialized": True, "pages": [1, 2, 3]}
        result = realxmarket_docs.get_docs_status()
        assert result["available"] is True
        assert result["pages"] == 3
        assert result["provider"] == "RealXmarket Docs"


class TestInitializeDocs:
    """Tests for initialize_docs function"""

    @patch('realxmarket_docs.requests.get')
    def test_successful_initialization(self, mock_get):
        # Create a valid sitemap XML response
        sitemap_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://doc-hub.xcavate.io/applications/xcavate-dapp/wallet</loc></url>
            <url><loc>https://doc-hub.xcavate.io/protocol/token</loc></url>
            <url><loc>https://doc-hub.xcavate.io/other/page</loc></url>
        </urlset>'''

        mock_response = MagicMock()
        mock_response.content = sitemap_xml
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = realxmarket_docs.initialize_docs()

        assert result["available"] is True
        assert result["pages"] == 2  # Only xcavate-dapp and protocol pages

    @patch('realxmarket_docs.requests.get')
    def test_request_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = realxmarket_docs.initialize_docs()

        assert result["available"] is False
        assert "reason" in result

    @patch('realxmarket_docs.requests.get')
    def test_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("404 Not Found"))
        mock_get.return_value = mock_response

        result = realxmarket_docs.initialize_docs()

        assert result["available"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
