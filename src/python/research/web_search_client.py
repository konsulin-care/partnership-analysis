"""
Web Search Client module for executing web searches using Google Gemini.

This module integrates with Google Gemini 2.5-flash to perform web searches
using the built-in GoogleSearch tool, with caching and retry logic.
"""

import hashlib
from typing import List, Dict, Any
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from google import genai
from google.genai import types
import structlog

from ..config.config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


def execute_web_search(queries: List[str], cache: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute web searches for a list of queries using Google Gemini with GoogleSearch tool.

    Checks cache first for each query. If not cached or stale, performs search with retries.
    Updates cache with new results.

    Args:
        queries: List of search query strings
        cache: Cache dictionary structure from CacheManager

    Returns:
        List of search result dictionaries, one per query, containing query, results, etc.
    """
    config = ConfigLoader()
    api_key = config.get('google_genai_api_key')
    logger.info("Initializing web search client", api_key_available=bool(api_key))
    if not api_key:
        raise ValueError("Google GenAI API key not configured")

    client = genai.Client(api_key=api_key)
    logger.info("Gemini client initialized")

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config_genai = types.GenerateContentConfig(
        tools=[grounding_tool], temperature=0.0
    )

    results = []
    for query in queries:
        logger.info("Processing query", query=query)
        query_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        cached = cache.get("research_queries", {}).get(query_hash)
        if cached and _is_cache_valid(cached):
            logger.info("Using cached results for query", query=query)
            results.append(cached)
            continue

        # Execute search
        logger.info("No valid cache, performing search for query", query=query)
        finding = _perform_search(client, config_genai, query)
        logger.info("Performed web search", query=query, results_count=len(finding))

        # Store in cache
        findings = {
            "query": query,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_days": 30,
            "results": finding['search_results'],
            "synthesis": finding['text']
        }
        cache.setdefault("research_queries", {})[query_hash] = findings
        logger.info("Cached search results", query_hash=query_hash)
        results.append(findings)

    return results


def _is_cache_valid(cached: Dict[str, Any]) -> bool:
    """Check if cached item is still valid based on TTL."""
    cached_at_str = cached.get("cached_at")
    if not cached_at_str:
        return False

    try:
        cached_at = datetime.fromisoformat(cached_at_str.replace('Z', '+00:00'))
    except ValueError:
        return False

    now = datetime.now(timezone.utc)
    age_days = (now - cached_at).days
    return age_days <= cached.get("ttl_days", 30)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _perform_search(client, config: types.GenerateContentConfig, query: str) -> Dict[str, Any]:
    """
    Perform a single web search using the Gemini client.

    Parses the response to extract search results.
    """
    logger.info("Sending search request to Gemini", query=query)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Search the web for: {query}",
        config=config,
    )
    logger.info("Received Gemini response", candidates_count=len(response.candidates) if response.candidates else 0)

    text = response.text
    search_results = []
    if hasattr(response, 'candidates'):
        for candidate in response.candidates:
            metadata = candidate.grounding_metadata
            chunks   = metadata.grounding_chunks
            supports = metadata.grounding_supports

            for support in supports:
                indices = support.grounding_chunk_indices
                urls = [chunks[index].web.uri for index in indices]
                titles = [chunks[index].web.title for index in indices]
                snippet = support.segment.text
                search_results.append({
                    'title': titles,
                    'url': urls,
                    'snippet': snippet,
                    'confidence': 0.85 # Placeholder
                })

    logger.info("Parsed search results", search_results_count=len(search_results))

    finding = {
        'text': text,
        'search_results': search_results
    }

    return finding
