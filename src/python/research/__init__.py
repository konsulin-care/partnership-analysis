"""
Research module for orchestrating web research and data extraction.

This module provides components for generating research queries, executing web searches,
parsing results, managing caches, and synthesizing findings for partnership analysis.
"""

from .query_generator import QueryGenerator
# from .web_search_client import WebSearchClient  # TODO: Implement
from .result_parser import parse_search_results, extract_structured_results
from .cache_manager import CacheManager
from .synthesizer import synthesize_market_data
# from .research_orchestrator import ResearchOrchestrator  # Import separately to avoid genai dependency

__all__ = ['QueryGenerator', 'parse_search_results', 'extract_structured_results', 'CacheManager', 'synthesize_market_data']