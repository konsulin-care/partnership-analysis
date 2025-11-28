"""
Research module for orchestrating web research and data extraction.

This module provides components for generating research queries, executing web searches,
parsing results, managing caches, and synthesizing findings for partnership analysis.

Key Features:
- QueryGenerator: Creates targeted search queries based on partner context
- WebSearchClient: Executes web searches using Google Gemini with caching
- CacheManager: Manages research result caching with TTL support
- ResearchOrchestrator: Coordinates the complete research workflow
- DeepResearchEngine: Performs iterative LLM-driven deep research
- LLMClient: Wrapper for Google Gemini models with research-specific methods

Deep Research Feature:
The deep research functionality enables iterative, LLM-enhanced research that:
- Extracts brand positioning from configuration data
- Performs up to 3 iterations of search, synthesis, and question generation
- Identifies research gaps and fills them automatically
- Provides comprehensive market analysis for partnership evaluation
"""

from .query_generator import QueryGenerator
from .web_search_client import execute_web_search
from .result_parser import parse_search_results, extract_structured_results
from .cache_manager import CacheManager
from .synthesizer import synthesize_market_data
from .research_orchestrator import ResearchOrchestrator
from .deep_research_engine import DeepResearchEngine
from .llm_client import LLMClient

__all__ = [
    'QueryGenerator',
    'execute_web_search',
    'parse_search_results',
    'extract_structured_results',
    'CacheManager',
    'synthesize_market_data',
    'ResearchOrchestrator',
    'DeepResearchEngine',
    'LLMClient'
]