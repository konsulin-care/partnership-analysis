"""
Deep Research Engine module for iterative, LLM-driven research.

This module implements the DeepResearchEngine class that conducts iterative research
using LLM adjustments, web searches, synthesis, and question generation to build
comprehensive research findings for partnership analysis.

Deep Research Feature Overview:
---------------------------
The deep research functionality provides an advanced, iterative approach to market research
that goes beyond basic web searches. It performs up to 3 iterations of research, where each
iteration includes:

1. Query Adjustment: LLM refines search terms based on previous findings and context
2. Web Search Execution: Performs targeted searches using adjusted queries
3. Findings Synthesis: LLM synthesizes search results into coherent insights
4. Gap Analysis: Generates follow-up questions to identify knowledge gaps
5. Iteration Control: Continues until gaps are filled or max iterations reached

Key Benefits:
- Automatic refinement of search strategies based on intermediate results
- Identification and filling of research gaps without manual intervention
- Comprehensive synthesis that combines findings across multiple iterations
- Brand-specific positioning extraction for tailored partnership analysis
- Caching of complete research workflows to avoid redundant work

Usage:
    engine = DeepResearchEngine()
    results = engine.conduct_deep_research(brand_config)
    # Results include iterations, findings, synthesis, and metadata

The deep research mode is particularly valuable for complex partnership evaluations
where understanding nuanced market positioning and competitive dynamics is crucial.
"""

import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog

from .llm_client import LLMClient, LLMClientError
from .query_generator import QueryGenerator
from .cache_manager import CacheManager
from .web_search_client import execute_web_search
from ..config.config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


class DeepResearchEngine:
    """
    Engine for conducting iterative, deep research using LLM and web search tools.

    Performs up to 3 iterations of research, adjusting search terms, executing searches,
    synthesizing findings, and generating follow-up questions to fill knowledge gaps.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        query_generator: Optional[QueryGenerator] = None,
        cache_manager: Optional[CacheManager] = None,
        config: Optional[ConfigLoader] = None
    ):
        """
        Initialize the DeepResearchEngine with dependencies.

        Args:
            llm_client: LLMClient instance for LLM operations
            query_generator: QueryGenerator instance for query generation
            cache_manager: CacheManager instance for caching
            config: ConfigLoader instance for configuration
        """
        self.llm_client = llm_client or LLMClient()
        self.query_generator = query_generator or QueryGenerator(self.llm_client)
        self.cache_manager = cache_manager or CacheManager()
        self.config = config or ConfigLoader()

        # Configuration parameters
        self.max_iterations = self.config.get('max_deep_research_iterations', 3)
        self.iteration_timeout = self.config.get('deep_research_iteration_timeout', 300)  # seconds
        self.min_questions_for_gap = self.config.get('min_questions_for_research_gap', 1)

        logger.info("DeepResearchEngine initialized", max_iterations=self.max_iterations)

    def conduct_deep_research(self, brand_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct iterative deep research based on brand configuration.

        Args:
            brand_config: Dictionary containing brand information

        Returns:
            Dictionary with comprehensive research results including iterations, findings, and final synthesis
        """
        brand_hash = self._hash_brand_config(brand_config)
        logger.info("Starting deep research", brand_hash=brand_hash)

        # Check cache for complete research
        cached_result = self._get_cached_deep_research(brand_hash)
        if cached_result:
            logger.info("Using cached deep research results", brand_hash=brand_hash)
            return cached_result

        # Generate initial queries
        initial_queries = self.query_generator.generate_brand_research_queries(brand_config)
        logger.info("Generated initial queries", query_count=len(initial_queries))

        all_findings = []
        current_queries = initial_queries
        iteration_results = []

        for iteration in range(self.max_iterations):
            logger.info("Starting research iteration", iteration=iteration + 1, max_iterations=self.max_iterations)

            try:
                # Adjust search terms
                adjusted_queries = self._adjust_search_terms(current_queries, brand_config)
                logger.info("Adjusted search terms", iteration=iteration + 1, query_count=len(adjusted_queries))

                # Execute research
                search_results = self._execute_research(adjusted_queries)
                logger.info("Executed research", iteration=iteration + 1, results_count=len(search_results))

                # Synthesize findings for this iteration
                iteration_synthesis = self._synthesize_iteration_findings(search_results)
                logger.info("Synthesized iteration findings", iteration=iteration + 1)

                # Generate further questions
                further_questions = self._generate_further_questions(brand_config, iteration_synthesis)
                logger.info("Generated further questions", iteration=iteration + 1, question_count=len(further_questions))

                # Store iteration results
                iteration_data = {
                    'iteration': iteration + 1,
                    'adjusted_queries': adjusted_queries,
                    'search_results': search_results,
                    'synthesis': iteration_synthesis,
                    'further_questions': further_questions,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                iteration_results.append(iteration_data)
                all_findings.extend(search_results)

                # Check for research gaps
                if not self._has_research_gaps(further_questions):
                    logger.info("No research gaps detected, stopping iterations", iteration=iteration + 1)
                    break

                # Prepare queries for next iteration from questions
                current_queries = self._questions_to_queries(further_questions, brand_config)
                logger.info("Prepared queries for next iteration", next_query_count=len(current_queries))

            except Exception as e:
                logger.error("Error in research iteration", iteration=iteration + 1, error=str(e))
                # Continue to next iteration or break based on error type
                if isinstance(e, LLMClientError):
                    logger.warning("LLM error, attempting to continue with next iteration")
                    continue
                else:
                    break

        # Final synthesis
        final_synthesis = self._perform_final_synthesis(all_findings, brand_config)
        logger.info("Completed final synthesis")

        # Prepare result
        result = {
            'brand_hash': brand_hash,
            'brand_config': brand_config,
            'iterations': iteration_results,
            'all_findings': all_findings,
            'final_synthesis': final_synthesis,
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'total_iterations': len(iteration_results)
        }

        # Cache the result
        self._cache_deep_research_result(brand_hash, result)
        logger.info("Cached deep research result", brand_hash=brand_hash)

        return result

    def _hash_brand_config(self, brand_config: Dict[str, Any]) -> str:
        """
        Generate hash for brand configuration.

        Args:
            brand_config: Brand configuration dictionary

        Returns:
            SHA256 hash as hexadecimal string
        """
        config_str = str(sorted(brand_config.items()))
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()

    def _get_cached_deep_research(self, brand_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached deep research result.

        Args:
            brand_hash: Hash of the brand configuration

        Returns:
            Cached deep research result if available, None otherwise
        """
        cached = self.cache_manager.get_cached_result(f"deep_research_{brand_hash}")
        return cached.get('result') if cached else None

    def _cache_deep_research_result(self, brand_hash: str, result: Dict[str, Any]) -> None:
        """
        Cache deep research result.

        Args:
            brand_hash: Hash of the brand configuration
            result: Complete deep research result to cache
        """
        cache_key = f"deep_research_{brand_hash}"
        findings = {
            'query': f"deep_research_{brand_hash}",
            'result': result
        }
        self.cache_manager.cache_research_findings(cache_key, findings)

    def _adjust_search_terms(self, queries: List[str], brand_config: Dict[str, Any]) -> List[str]:
        """
        Adjust search terms using LLM for better research results.

        Args:
            queries: Original search queries
            brand_config: Brand configuration for context

        Returns:
            List of adjusted search queries
        """
        adjusted = []
        context = f"Brand: {brand_config.get('BRAND_NAME', '')}, Industry: {brand_config.get('BRAND_INDUSTRY', '')}"
        for query in queries:
            try:
                adjusted_query = self.llm_client.adjust_search_terms(query, context)
                adjusted.append(adjusted_query)
            except LLMClientError as e:
                logger.warning("Failed to adjust search term, using original", query=query, error=str(e))
                adjusted.append(query)
        return adjusted

    def _execute_research(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute web research for the given queries.

        Args:
            queries: List of search queries to execute

        Returns:
            List of search result dictionaries
        """
        cache = self.cache_manager.cache
        return execute_web_search(queries, cache, research_context=True)

    def _synthesize_iteration_findings(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Synthesize findings from the current iteration.

        Args:
            search_results: Results from the current iteration's searches

        Returns:
            Synthesized narrative of the findings
        """
        findings = []
        for result in search_results:
            findings.append({
                'query': result.get('query', ''),
                'results': result.get('results', []),
                'synthesis': result.get('synthesis', '')
            })
        try:
            return self.llm_client.synthesize_findings(findings)
        except LLMClientError as e:
            logger.warning("Failed to synthesize findings", error=str(e))
            return "Synthesis failed due to LLM error."

    def _generate_further_questions(self, brand_config: Dict[str, Any], synthesis: str) -> List[str]:
        """
        Generate further research questions based on current synthesis.

        Args:
            brand_config: Brand configuration for context
            synthesis: Current synthesis of findings

        Returns:
            List of follow-up research questions
        """
        topic = f"Partnership analysis for {brand_config.get('BRAND_NAME', '')} in {brand_config.get('BRAND_INDUSTRY', '')}"
        context = f"Current findings: {synthesis}"
        try:
            return self.llm_client.generate_questions(topic, context)
        except LLMClientError as e:
            logger.warning("Failed to generate further questions", error=str(e))
            return []

    def _has_research_gaps(self, questions: List[str]) -> bool:
        """
        Determine if there are research gaps based on generated questions.

        Args:
            questions: List of generated questions

        Returns:
            True if there are enough questions to indicate research gaps
        """
        return len(questions) >= self.min_questions_for_gap

    def _questions_to_queries(self, questions: List[str], brand_config: Dict[str, Any]) -> List[str]:
        """
        Convert research questions back into search queries.

        Args:
            questions: List of research questions
            brand_config: Brand configuration for context

        Returns:
            List of search queries derived from questions
        """
        queries = []
        for question in questions:
            # Simple conversion: use question as base for query
            query = f"{question} {brand_config.get('BRAND_INDUSTRY', '')} {brand_config.get('BRAND_ADDRESS', '')}"
            queries.append(query)
        return queries

    def _perform_final_synthesis(self, all_findings: List[Dict[str, Any]], brand_config: Dict[str, Any]) -> str:
        """
        Perform final synthesis of all research findings across iterations.

        Args:
            all_findings: All search results from all iterations
            brand_config: Brand configuration for tailored analysis

        Returns:
            Final comprehensive synthesis tailored to partnership analysis
        """
        findings = []
        for result in all_findings:
            findings.append({
                'query': result.get('query', ''),
                'results': result.get('results', []),
                'synthesis': result.get('synthesis', '')
            })
        try:
            synthesis = self.llm_client.synthesize_findings(findings)
            # Enhance with brand context
            final_prompt = f"""
            Based on the comprehensive research synthesis below, provide a final analysis
            specifically tailored for partnership opportunities with {brand_config.get('BRAND_NAME', '')}
            in the {brand_config.get('BRAND_INDUSTRY', '')} industry at {brand_config.get('BRAND_ADDRESS', '')}.

            Research Synthesis:
            {synthesis}

            Focus on key insights relevant to business partnerships, market positioning, and growth opportunities.
            """
            return self.llm_client.execute_prompt('gemini-2.5-flash', final_prompt, temperature=0.4, max_tokens=1024)
        except LLMClientError as e:
            logger.warning("Failed to perform final synthesis", error=str(e))
            return "Final synthesis failed due to LLM error."