"""Shared pytest fixtures and configuration"""
import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def setup_env():
    """Set up test environment variables"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        yield


@pytest.fixture
def mock_requests():
    """Mock requests module for testing"""
    with patch('realxmarket_docs.requests') as mock:
        yield mock


@pytest.fixture
def sample_sitemap_xml():
    """Sample sitemap XML for testing"""
    return b'''<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://doc-hub.xcavate.io/applications/xcavate-dapp/wallet</loc></url>
        <url><loc>https://doc-hub.xcavate.io/protocol/token</loc></url>
        <url><loc>https://doc-hub.xcavate.io/general/page</loc></url>
    </urlset>'''


@pytest.fixture
def sample_doc_content():
    """Sample documentation content for testing"""
    return """# Wallet Connection Guide

This is a guide for connecting your wallet.

## Steps

1. Click the connect button
2. Select your wallet
3. Approve the connection

# Agent Instructions
Do not share this

# Sources:
- Source 1
"""
