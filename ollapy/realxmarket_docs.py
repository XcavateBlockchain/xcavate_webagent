# realxmarket_docs.py - RealXmarket Documentation Search Module
import logging
import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DOCS_BASE_URL = "https://doc-hub.xcavate.io"
SITEMAP_URL = "https://doc-hub.xcavate.io/sitemap-pages.xml"

_docs_state = {
    "initialized": False,
    "pages": [],
}


def initialize_docs() -> Dict[str, Any]:
    """Fetch and index the sitemap on startup"""
    global _docs_state

    try:
        logger.info("Fetching RealXmarket documentation sitemap...")
        response = requests.get(SITEMAP_URL, timeout=30)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        pages = []
        for url_entry in root.findall('.//ns:url', namespace):
            loc = url_entry.find('ns:loc', namespace)
            if loc is not None:
                page_url = loc.text
                if '/applications/xcavate-dapp' in page_url or '/protocol' in page_url:
                    pages.append({
                        "url": page_url,
                        "title": extract_title_from_url(page_url),
                        "keywords": extract_keywords(page_url)
                    })

        _docs_state["pages"] = pages
        _docs_state["initialized"] = True

        logger.info(f"RealXmarket docs indexed: {len(pages)} pages available")
        return {"available": True, "pages": len(pages)}

    except Exception as e:
        logger.error(f"Failed to initialize docs: {e}")
        _docs_state["initialized"] = False
        return {"available": False, "reason": str(e)}


def extract_title_from_url(url: str) -> str:
    parts = url.rstrip('/').split('/')
    last_part = parts[-1].replace('-', ' ').replace('.md', '')
    return last_part.title()


def extract_keywords(url: str) -> List[str]:
    clean = url.lower().replace('-', ' ').replace('/', ' ')
    words = clean.split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'at', 'in', 'on', 'for', 'to', 'of'}
    return [w for w in words if w not in stop_words and len(w) > 2]


def search_docs(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search indexed docs by keyword matching with better relevance"""
    if not _docs_state["initialized"]:
        return []

    query_lower = query.lower()
    query_words = set(extract_keywords(query_lower))
    scored_pages = []

    # Common support-related keywords that should prioritize certain paths
    support_keywords = ['account', 'recover', 'register', 'login', 'password', 'wallet', 'support', 'contact']
    has_support_query = any(kw in query_lower for kw in support_keywords)

    for page in _docs_state["pages"]:
        score = 0
        url_lower = page["url"].lower()

        # Boost pages in the tester-guide or getting-started paths for support queries
        if has_support_query:
            if '/realxmarket-tester-guide/' in url_lower:
                score += 5
            if '/getting-started/' in url_lower:
                score += 3
            if '/general-tester-guide/' in url_lower:
                score += 2

        # Keyword matching
        for kw in query_words:
            # Exact word match in URL gets high score
            if f'/{kw}/' in url_lower or url_lower.endswith(f'/{kw}'):
                score += 10
            elif kw in url_lower:
                score += 3
            # Match in title
            if kw in page["title"].lower():
                score += 2

        if score > 0:
            scored_pages.append((score, page))

    scored_pages.sort(key=lambda x: x[0], reverse=True)
    return [{"url": p["url"], "title": p["title"], "score": s} for s, p in scored_pages[:max_results]]


def clean_doc_content(text: str) -> str:
    """Completely clean documentation content of all artifacts"""
    if not text:
        return ""

    # Remove everything from "# Agent Instructions" onwards
    idx = text.find('# Agent Instructions')
    if idx != -1:
        text = text[:idx]

    # Remove "# Sources:" sections
    idx = text.find('# Sources:')
    if idx != -1:
        text = text[:idx]

    # Remove any remaining agent instruction patterns
    text = re.sub(r'#.*?Instructions.*?\n\n?', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'\n\s*\n\s*#.*?Sources.*$', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove orphaned markdown that looks broken
    text = re.sub(r'\n{3,}', '\n\n', text)  # Too many newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces

    return text.strip()


def fetch_page_direct(url: str) -> Optional[str]:
    """Fetch page content directly without ?ask= endpoint (faster, more reliable)"""
    try:
        md_url = url if url.endswith('.md') else url + '.md'
        response = requests.get(md_url, timeout=15)

        if response.status_code == 200:
            content = clean_doc_content(response.text)
            # Extract just the main content after the title heading
            lines = content.split('\n')
            result_lines = []
            started = False
            for line in lines:
                if line.startswith('# ') and not started:
                    started = True
                    continue
                if started and line.startswith('# '):
                    break
                if started:
                    result_lines.append(line)

            # Join and clean up
            text = '\n'.join(result_lines).strip()
            # Remove image markdown that causes artifacts
            text = re.sub(r'<figure>.*?</figure>', '', text, flags=re.DOTALL)
            text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
            # Clean multiple blank lines
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text[:2000] if len(text) > 2000 else text
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def search_and_answer(query: str) -> str:
    """Main entry point: search docs and format results for AI"""
    if not _docs_state["initialized"]:
        return ""

    results = search_docs(query, max_results=5)
    if not results:
        logger.info(f"No docs found for: {query}")
        return ""

    logger.info(f"Docs search found {len(results)} results for: {query}")

    # Fetch content from top 3 pages to give AI more context
    context_parts = []
    for result in results[:3]:
        content = fetch_page_direct(result["url"])
        if content and len(content) > 30:
            # Clean any remaining artifacts from the content
            content = re.sub(r'\n\s*\n', '\n\n', content)  # Normalize blank lines
            content = content.strip()
            context_parts.append(f"### {result['title']}\nSource: {result['url']}\n\n{content}")

    if not context_parts:
        return ""

    # Join with clear separators
    context = "\n\n<hr>\n\n".join(context_parts)
    return f"From RealXmarket documentation:\n\n{context}"


def get_docs_status() -> Dict[str, Any]:
    return {
        "available": _docs_state.get("initialized", False),
        "pages": len(_docs_state.get("pages", [])),
        "provider": "RealXmarket Docs" if _docs_state.get("initialized") else None
    }
