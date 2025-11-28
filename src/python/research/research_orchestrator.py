"""
Research Orchestrator module for coordinating web research and data extraction.

This module provides the ResearchOrchestrator class that coordinates query generation,
cache checking, web search execution, result parsing, and synthesis of market data.
"""

from typing import Dict, Any, List
import structlog

from .query_generator import QueryGenerator
from .cache_manager import CacheManager
from .web_search_client import execute_web_search
from .result_parser import parse_search_results, extract_structured_results
from .synthesizer import synthesize_market_data

logger = structlog.get_logger(__name__)


class ResearchOrchestrator:
    """
    Orchestrates the research process for partnership analysis.

    Coordinates query generation, cache management, web search execution,
    result parsing, and synthesis of market data from web research.
    """

    def __init__(self, query_generator: QueryGenerator = None, cache_manager: CacheManager = None):
        """
        Initialize the ResearchOrchestrator.

        Args:
            query_generator: Instance of QueryGenerator for creating search queries
            cache_manager: Instance of CacheManager for caching research results
        """
        self.query_generator = query_generator or QueryGenerator()
        self.cache_manager = cache_manager or CacheManager()

    def orchestrate_research(self, partner_type: str, industry: str, location: str) -> Dict[str, Any]:
        """
        Orchestrate the complete research process following the architecture logic.

        For each research category needed:
        1. Generate 2-3 targeted search queries based on user context
        2. Check cache for identical or similar queries
        3. If cache hit: return cached result (verify freshness)
        4. If cache miss:
           a. Execute web search (up to 3 queries per category)
           b. Extract structured facts from search results
           c. Validate confidence scores for each finding
           d. Cache result with source attribution and timestamp
        5. Synthesize findings into coherent market narrative
        6. Flag low-confidence data for manual review

        Args:
            partner_type: Type of partner (e.g., 'clinic', 'spa', 'wellness center')
            industry: Industry sector (e.g., 'medical aesthetics', 'wellness')
            location: Geographic location (e.g., 'Indonesia', 'Jakarta')

        Returns:
            Dictionary containing synthesized market data with benchmarks, sources, and confidence scores
        """
        logger.info("Starting research orchestration", partner_type=partner_type, industry=industry, location=location)

        # Step 1: Generate research queries
        queries = self.query_generator.generate_research_queries(partner_type, industry, location)
        logger.info("Generated research queries", queries=queries)

        all_findings = []

        # Step 2-4: Process each query
        for query in queries:
            query_hash = self.cache_manager.hash_query(query)
            logger.info("Processing query", query=query, query_hash=query_hash)
            cached = self.cache_manager.get_cached_result(query_hash)

            if cached:
                # Cache hit: use cached results
                logger.info("Cache hit for query", query=query)
                parsed_results = cached.get('results', [])
            else:
                # Cache miss: execute web search
                logger.info("Cache miss for query, executing search", query=query)
                search_results = execute_web_search([query], self.cache_manager.cache)
                logger.info("Executed web search", query=query, results_count=len(search_results))

                # Parse search results
                parsed = parse_search_results(search_results)
                parsed_results = parsed.get('parsed_results', [])
                logger.info("Parsed search results", parsed_results_count=len(parsed_results))

                # Cache the findings
                findings = {
                    'query': query,
                    'results': parsed_results,
                    'synthesis': ''
                }
                self.cache_manager.cache_research_findings(query_hash, findings)
                logger.info("Cached research findings", query_hash=query_hash)

            # Step 4b: Extract structured facts (placeholder extraction)
            # Convert parsed results to findings format for synthesis
            for result in parsed_results:
                finding = {
                    'benchmark_type': 'general',  # Placeholder - would be extracted by extractors module
                    'value': result.get('snippet', ''),
                    'confidence': result.get('confidence', 0.5),
                    'source': result.get('url', '')
                }
                all_findings.append(finding)

        # Step 5: Synthesize findings into market data
        synthesized_data = synthesize_market_data(all_findings)
        logger.info("Synthesized market data", synthesized_data_keys=list(synthesized_data.keys()))

        # Step 6: Flag low-confidence data for manual review
        if synthesized_data.get('overall', {}).get('average_confidence', 0.0) < 0.7:
            synthesized_data['flags'] = ['low_confidence_data_detected']
            logger.info("Flagged low-confidence data", flags=synthesized_data['flags'])

        logger.info("Research orchestration completed", overall_confidence=synthesized_data.get('overall', {}).get('average_confidence', 0.0))
        return synthesized_data