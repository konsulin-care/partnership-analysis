"""
Result Parser module for parsing web search results into structured JSON.

This module takes the output from the web search client and parses it into
a standardized structured format with titles, URLs, snippets, and confidence scores.
"""

from typing import List, Dict, Any


def parse_search_results(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse web search results into structured JSON format.

    Takes the list of search result dictionaries from execute_web_search and
    extracts/parses them into a standardized structure for further processing.

    Args:
        search_results: List of search result dictionaries from web_search_client

    Returns:
        Dictionary containing parsed results with standardized structure:
        {
            "parsed_results": List[Dict] - List of individual result items
            "total_results": int - Total number of results across all queries
            "queries_processed": int - Number of queries processed
        }
    """
    parsed_results = []
    total_results = 0
    queries_processed = len(search_results)

    for result_item in search_results:
        query = result_item.get("query", "")
        results = result_item.get("results", [])

        for result in results:
            # Ensure all required fields are present and standardized
            parsed_result = {
                "query": query,
                "title": str(result.get("title") or "").strip(),
                "url": str(result.get("url") or "").strip(),
                "snippet": str(result.get("snippet") or "").strip(),
                "confidence": result.get("confidence", 0.5)  # Default to 0.5 if not present
            }

            # Ensure confidence is a number
            if not isinstance(parsed_result["confidence"], (int, float)):
                parsed_result["confidence"] = 0.5

            # Validate URL format (basic check)
            if not parsed_result["url"].startswith(("http://", "https://")):
                parsed_result["confidence"] *= 0.8  # Reduce confidence for invalid URLs

            # Validate content presence
            if not parsed_result["title"] or not parsed_result["snippet"]:
                parsed_result["confidence"] *= 0.9  # Slight reduction for missing content

            parsed_results.append(parsed_result)
            total_results += 1

    return {
        "parsed_results": parsed_results,
        "total_results": total_results,
        "queries_processed": queries_processed
    }


def extract_structured_results(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract structured results from search data.

    Alias for parse_search_results for consistency with architecture.
    """
    return parse_search_results(search_results)