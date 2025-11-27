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

from ..config.config_loader import ConfigLoader


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
    if not api_key:
        raise ValueError("Google GenAI API key not configured")

    client = genai.Client(api_key=api_key)

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config_genai = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    results = []
    for query in queries:
        query_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        cached = cache.get("research_queries", {}).get(query_hash)
        if cached and _is_cache_valid(cached):
            results.append(cached)
            continue

        # Execute search
        search_result = _perform_search(client, config_genai, query)

        # Store in cache
        findings = {
            "query": query,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_days": 30,
            "results": search_result,
            "synthesis": ""  # Synthesis can be added later if needed
        }
        cache.setdefault("research_queries", {})[query_hash] = findings
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
def _perform_search(client, config: types.GenerateContentConfig, query: str) -> List[Dict[str, Any]]:
    """
    Perform a single web search using the Gemini client.

    Parses the response to extract search results.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Search the web for: {query}",
        config=config,
    )

    search_results = []
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_response') and part.function_response:
                        func_resp = part.function_response
                        if hasattr(func_resp, 'response') and 'results' in func_resp.response:
                            for result in func_resp.response['results']:
                                search_results.append({
                                    'title': result.get('title', ''),
                                    'url': result.get('url', ''),
                                    'snippet': result.get('snippet', ''),
                                    'confidence': 0.85  # Default confidence score
                                })
    return search_results
