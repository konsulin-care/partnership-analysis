"""
Integration tests for end-to-end deep research workflow.

Tests the complete deep research pipeline from brand configuration to final synthesis,
including multi-iteration research, cache integration, error recovery, and performance validation.
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone

from src.python.research.deep_research_engine import DeepResearchEngine
from src.python.research.llm_client import LLMClient, LLMClientError
from src.python.research.query_generator import QueryGenerator
from src.python.research.cache_manager import CacheManager
from src.python.config.config_loader import ConfigLoader


@pytest.fixture
def sample_brand_configs():
    """Realistic brand configuration fixtures for testing."""
    return {
        "medical_aesthetics_clinic": {
            "BRAND_NAME": "Glow Aesthetics Clinic",
            "BRAND_INDUSTRY": "medical_aesthetics",
            "BRAND_ADDRESS": "Jakarta, Indonesia",
            "BRAND_DESCRIPTION": "Premium medical aesthetics clinic specializing in hair transplants, skincare treatments, and cosmetic procedures",
            "BRAND_TARGET_MARKET": "Middle to high-income individuals aged 25-55 seeking cosmetic enhancements",
            "BRAND_POSITIONING": "Luxury medical aesthetics with cutting-edge technology and personalized care",
            "BRAND_ESTABLISHED": "2023",
            "BRAND_SIZE": "2000 sqm facility with 15 treatment rooms"
        },
        "wellness_hub_partner": {
            "BRAND_NAME": "Harmony Wellness Hub",
            "BRAND_INDUSTRY": "wellness",
            "BRAND_ADDRESS": "Surabaya, Indonesia",
            "BRAND_DESCRIPTION": "Comprehensive wellness center offering medical aesthetics, fitness, nutrition, and holistic health services",
            "BRAND_TARGET_MARKET": "Health-conscious individuals and families seeking integrated wellness solutions",
            "BRAND_POSITIONING": "One-stop wellness destination combining medical expertise with lifestyle coaching",
            "BRAND_ESTABLISHED": "2020",
            "BRAND_SIZE": "5000 sqm multi-level facility"
        },
        "dental_clinic": {
            "BRAND_NAME": "SmilePerfect Dental",
            "BRAND_INDUSTRY": "dental_care",
            "BRAND_ADDRESS": "Bandung, Indonesia",
            "BRAND_DESCRIPTION": "Modern dental clinic specializing in cosmetic dentistry, orthodontics, and implant procedures",
            "BRAND_TARGET_MARKET": "Urban professionals and families seeking high-quality dental care",
            "BRAND_POSITIONING": "Advanced dental technology with patient-centered care approach",
            "BRAND_ESTABLISHED": "2022",
            "BRAND_SIZE": "800 sqm clinic with digital imaging equipment"
        }
    }


@pytest.fixture
def mock_search_results():
    """Mock search results for different research queries."""
    return {
        "pricing_results": [
            {
                "query": "medical aesthetics clinic pricing Indonesia 2025",
                "results": [
                    {
                        "title": "Indonesia Medical Aesthetics Market Report 2025",
                        "url": "https://example.com/report",
                        "snippet": "Hair transplant procedures range from IDR 15.8M to 47.4M with average costs around IDR 30M. Market growth rate of 15% annually.",
                        "confidence": 0.85
                    }
                ],
                "synthesis": "Market pricing shows competitive range between IDR 15.8M-47.4M with 15% annual growth"
            }
        ],
        "market_results": [
            {
                "query": "Indonesia wellness market size 2025",
                "results": [
                    {
                        "title": "Wellness Industry Analysis Indonesia",
                        "url": "https://marketresearch.com/indonesia-wellness",
                        "snippet": "The Indonesian wellness market is valued at IDR 25T with 12% annual growth rate. Medical tourism contributes significantly.",
                        "confidence": 0.80
                    }
                ],
                "synthesis": "Wellness market valued at IDR 25T with 12% growth, strong medical tourism component"
            }
        ],
        "competition_results": [
            {
                "query": "medical aesthetics clinic competition Jakarta",
                "results": [
                    {
                        "title": "Jakarta Aesthetics Market Competition",
                        "url": "https://competition-analysis.com/jakarta",
                        "snippet": "Over 200 medical aesthetics clinics in Jakarta with premium positioning commanding 30-50% higher prices.",
                        "confidence": 0.75
                    }
                ],
                "synthesis": "Highly competitive market with 200+ clinics, premium positioning justifies higher pricing"
            }
        ]
    }


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for different operations."""
    return {
        "adjusted_queries": [
            "medical aesthetics clinic pricing Indonesia 2025 market analysis",
            "wellness industry growth rates Jakarta 2025",
            "medical aesthetics competition analysis Indonesia"
        ],
        "synthesis": "Comprehensive market analysis reveals strong growth potential in Indonesia's medical aesthetics sector with pricing ranging from IDR 15.8M-47.4M for procedures. Market shows 12-15% annual growth with increasing demand for premium services.",
        "further_questions": [
            "What are the regulatory requirements for medical aesthetics clinics in Indonesia?",
            "How do operational costs compare between standalone clinics and wellness hubs?",
            "What is the impact of medical tourism on local market pricing?"
        ],
        "final_synthesis": "Based on comprehensive research, Glow Aesthetics Clinic demonstrates strong partnership potential with Harmony Wellness Hub. The medical aesthetics market in Jakarta shows robust growth with premium pricing positioning that aligns well with hub's luxury positioning. Key partnership opportunities include shared patient base, combined service offerings, and cost efficiencies through hub infrastructure."
    }


class TestEndToEndDeepResearch:
    """Integration tests for complete deep research workflow."""

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_complete_deep_research_workflow(self, mock_execute_web_search,
                                           sample_brand_configs, mock_search_results,
                                           mock_llm_responses):
        """Test complete deep research workflow from brand config to final synthesis."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        # Setup mocks
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 2,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 2
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None  # No cache hit

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = [
            "medical aesthetics clinic pricing Indonesia 2025",
            "Indonesia wellness market size 2025"
        ]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.side_effect = lambda q, c: f"{q} analysis"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
        mock_llm.generate_questions.return_value = ["What are regulatory requirements?"]  # Below threshold
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        # Create engine
        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        # Execute research
        start_time = time.time()
        result = engine.conduct_deep_research(brand_config)
        execution_time = time.time() - start_time

        # Validate result structure
        assert 'brand_hash' in result
        assert result['brand_config'] == brand_config
        assert 'iterations' in result
        assert len(result['iterations']) == 1  # Single iteration due to question threshold
        assert 'all_findings' in result
        assert 'final_synthesis' in result
        assert 'completed_at' in result
        assert result['total_iterations'] == 1

        # Validate iteration structure
        iteration = result['iterations'][0]
        assert 'iteration' in iteration
        assert 'adjusted_queries' in iteration
        assert 'search_results' in iteration
        assert 'synthesis' in iteration
        assert 'further_questions' in iteration
        assert 'timestamp' in iteration

        # Validate final synthesis contains brand-specific content
        assert "Glow Aesthetics Clinic" in result['final_synthesis']
        assert "Harmony Wellness Hub" in result['final_synthesis']
        assert "partnership" in result['final_synthesis'].lower()

        # Performance assertion (should complete within reasonable time)
        assert execution_time < 5.0  # Less than 5 seconds for mocked execution

        # Verify cache was checked and result stored
        mock_cache.get_cached_result.assert_called_once()
        mock_cache.cache_research_findings.assert_called_once()

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_multi_iteration_research_with_gap_detection(self, mock_execute_web_search,
                                                        sample_brand_configs, mock_search_results,
                                                        mock_llm_responses):
        """Test multi-iteration research with gap detection and question generation."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        # Setup mocks
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 3,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 1
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = ["initial query"]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.side_effect = lambda q, c: f"adjusted_{q}"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]

        # First iteration: generate questions (triggers next iteration)
        # Second iteration: no more questions (stops iteration)
        mock_llm.generate_questions.side_effect = [
            mock_llm_responses["further_questions"],  # Iteration 1: has gaps
            []  # Iteration 2: no gaps
        ]
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        # Mock different search results for each iteration
        mock_execute_web_search.side_effect = [
            mock_search_results["pricing_results"],  # Iteration 1
            mock_search_results["market_results"]    # Iteration 2
        ]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        result = engine.conduct_deep_research(brand_config)

        # Should have 2 iterations
        assert len(result['iterations']) == 2
        assert result['total_iterations'] == 2

        # Verify first iteration
        iter1 = result['iterations'][0]
        assert iter1['iteration'] == 1
        assert len(iter1['further_questions']) >= 1

        # Verify second iteration
        iter2 = result['iterations'][1]
        assert iter2['iteration'] == 2
        assert len(iter2['further_questions']) == 0

        # Verify LLM calls
        assert mock_llm.generate_questions.call_count == 2
        assert mock_execute_web_search.call_count == 2

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_cache_integration_across_iterations(self, mock_execute_web_search,
                                                sample_brand_configs, mock_search_results,
                                                mock_llm_responses):
        """Test cache integration across multiple research sessions."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 1,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 2
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None  # No initial cache

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = ["test query"]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.return_value = "adjusted_test query"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
        mock_llm.generate_questions.return_value = []
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        # First research execution
        result1 = engine.conduct_deep_research(brand_config)

        # Verify result was cached
        assert mock_cache.cache_research_findings.call_count == 1

        # Reset mocks for second execution
        mock_cache.reset_mock()
        mock_query_gen.reset_mock()
        mock_llm.reset_mock()
        mock_execute_web_search.reset_mock()

        # Mock cache hit for second execution
        mock_cache.get_cached_result.return_value = {'result': result1}

        # Second research execution (same brand config)
        result2 = engine.conduct_deep_research(brand_config)

        # Verify cache was used (no new research performed)
        assert result2 == result1
        mock_cache.get_cached_result.assert_called_once()
        mock_query_gen.generate_brand_research_queries.assert_not_called()
        mock_llm.adjust_search_terms.assert_not_called()
        mock_execute_web_search.assert_not_called()

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_error_recovery_and_graceful_degradation(self, mock_execute_web_search,
                                                    sample_brand_configs, mock_search_results):
        """Test error recovery and graceful degradation."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 2,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 2
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = ["test query"]

        mock_llm = MagicMock()
        # LLM fails on adjustment but succeeds on synthesis
        mock_llm.adjust_search_terms.side_effect = LLMClientError("API temporarily unavailable")
        mock_llm.synthesize_findings.return_value = "Synthesis completed despite adjustment failure"
        mock_llm.generate_questions.return_value = []
        mock_llm.execute_prompt.return_value = "Final synthesis with error recovery"

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        result = engine.conduct_deep_research(brand_config)

        # Should complete despite LLM adjustment failure
        assert 'final_synthesis' in result
        assert result['total_iterations'] == 1

        # Verify original queries were used as fallback
        iteration = result['iterations'][0]
        assert "test query" in iteration['adjusted_queries'][0]  # Original query used

        # Verify synthesis still occurred
        assert "Synthesis completed despite adjustment failure" in iteration['synthesis']

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_configuration_parameter_validation_and_usage(self, mock_execute_web_search,
                                                         sample_brand_configs, mock_search_results,
                                                         mock_llm_responses):
        """Test configuration parameter validation and usage."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        # Test with various config parameters
        test_configs = [
            {'max_deep_research_iterations': 1, 'min_questions_for_research_gap': 1},
            {'max_deep_research_iterations': 3, 'min_questions_for_research_gap': 5},
            {'max_deep_research_iterations': 2, 'min_questions_for_research_gap': 2}
        ]

        for i, config_params in enumerate(test_configs):
            mock_config = MagicMock()
            mock_config.get.side_effect = lambda key, default=None: config_params.get(key, default)

            mock_cache = MagicMock()
            mock_cache.get_cached_result.return_value = None

            mock_query_gen = MagicMock()
            mock_query_gen.generate_brand_research_queries.return_value = ["test query"]

            mock_llm = MagicMock()
            mock_llm.adjust_search_terms.return_value = "adjusted_test query"
            mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
            # For the first config, generate enough questions to trigger max iterations
            # For others, generate fewer questions
            if i == 1:  # max_iterations=3, min_questions=5
                questions = ["q1", "q2", "q3", "q4", "q5"]  # Exactly at threshold
            else:
                questions = ["q1"] * (config_params['min_questions_for_research_gap'] - 1)  # Below threshold
            mock_llm.generate_questions.return_value = questions
            mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

            mock_execute_web_search.return_value = mock_search_results["pricing_results"]

            engine = DeepResearchEngine(
                llm_client=mock_llm,
                query_generator=mock_query_gen,
                cache_manager=mock_cache,
                config=mock_config
            )

            result = engine.conduct_deep_research(brand_config)

            # Verify config parameters were used correctly
            assert result['total_iterations'] <= config_params['max_deep_research_iterations']

            # Verify question threshold logic
            if len(questions) >= config_params['min_questions_for_research_gap']:
                # Should attempt max iterations
                assert result['total_iterations'] == config_params['max_deep_research_iterations']
            else:
                # Should stop at 1 iteration
                assert result['total_iterations'] == 1

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_brand_positioning_extraction_and_usage_in_queries(self, mock_execute_web_search,
                                                              sample_brand_configs, mock_search_results,
                                                              mock_llm_responses):
        """Test brand positioning extraction and usage in queries."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 1,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 2
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = [
            "medical aesthetics clinic pricing Indonesia 2025",
            "luxury medical aesthetics positioning Jakarta"
        ]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.side_effect = lambda q, c: f"{q} premium luxury analysis"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
        mock_llm.generate_questions.return_value = []
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        result = engine.conduct_deep_research(brand_config)

        # Verify brand positioning was incorporated into queries
        iteration = result['iterations'][0]
        adjusted_queries = iteration['adjusted_queries']

        # Check that positioning terms were added
        assert any("premium luxury analysis" in query for query in adjusted_queries)

        # Verify LLM received brand context
        adjust_calls = mock_llm.adjust_search_terms.call_args_list
        for call_args in adjust_calls:
            query, context = call_args[0]
            assert "Glow Aesthetics Clinic" in context
            assert "medical_aesthetics" in context

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_final_synthesis_tailored_to_partnership_opportunities(self, mock_execute_web_search,
                                                                  sample_brand_configs, mock_search_results,
                                                                  mock_llm_responses):
        """Test final synthesis tailored to partnership opportunities."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 1,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 2
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = ["test query"]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.return_value = "adjusted_test query"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
        mock_llm.generate_questions.return_value = []
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        result = engine.conduct_deep_research(brand_config)

        # Verify final synthesis call
        assert mock_llm.execute_prompt.call_count == 1
        call_args = mock_llm.execute_prompt.call_args
        args, kwargs = call_args
        model, prompt = args[0], args[1]
        temperature = kwargs.get('temperature', 0.4)
        max_tokens = kwargs.get('max_tokens', 1024)

        # Verify prompt contains partnership-focused content
        assert "partnership opportunities" in prompt.lower()
        assert "business partnerships" in prompt.lower()
        assert "growth opportunities" in prompt.lower()

        # Verify brand-specific tailoring
        assert "Glow Aesthetics Clinic" in prompt
        assert "medical_aesthetics" in prompt
        assert "Jakarta, Indonesia" in prompt

        # Verify research synthesis was included
        assert mock_llm_responses["synthesis"] in prompt

        # Verify result contains tailored synthesis
        assert result['final_synthesis'] == mock_llm_responses["final_synthesis"]
        assert "partnership potential" in result['final_synthesis'].lower()

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_performance_assertions_and_result_validation(self, mock_execute_web_search,
                                                         sample_brand_configs, mock_search_results,
                                                         mock_llm_responses):
        """Test performance assertions and result structure validation."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 2,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 1
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = ["test query"]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.return_value = "adjusted_test query"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
        mock_llm.generate_questions.side_effect = [
            mock_llm_responses["further_questions"],  # Triggers second iteration
            []  # Stops after second iteration
        ]
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        # Measure performance
        start_time = time.time()
        result = engine.conduct_deep_research(brand_config)
        execution_time = time.time() - start_time

        # Performance assertions (relaxed for mocked tests)
        assert execution_time < 10.0  # Should complete within 10 seconds
        assert execution_time >= 0.0  # Should take non-negative time

        # Comprehensive result structure validation
        required_keys = [
            'brand_hash', 'brand_config', 'iterations', 'all_findings',
            'final_synthesis', 'completed_at', 'total_iterations'
        ]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

        # Validate brand hash is SHA256
        assert len(result['brand_hash']) == 64
        import string
        assert all(c in string.hexdigits for c in result['brand_hash'])  # Hex characters only

        # Validate iterations structure
        assert isinstance(result['iterations'], list)
        assert len(result['iterations']) > 0
        for iteration in result['iterations']:
            iteration_keys = ['iteration', 'adjusted_queries', 'search_results',
                            'synthesis', 'further_questions', 'timestamp']
            for key in iteration_keys:
                assert key in iteration, f"Missing iteration key: {key}"
            assert isinstance(iteration['iteration'], int)
            assert isinstance(iteration['adjusted_queries'], list)
            assert isinstance(iteration['search_results'], list)

        # Validate timestamp format
        for iteration in result['iterations']:
            datetime.fromisoformat(iteration['timestamp'].replace('Z', '+00:00'))

        # Validate completed_at timestamp
        datetime.fromisoformat(result['completed_at'].replace('Z', '+00:00'))

        # Validate final synthesis is not empty and contains expected content
        assert len(result['final_synthesis']) > 50
        assert "partnership" in result['final_synthesis'].lower()

        # Validate total iterations matches iterations list
        assert result['total_iterations'] == len(result['iterations'])

    @patch('src.python.research.deep_research_engine.execute_web_search')
    def test_result_structure_matches_expected_schema(self, mock_execute_web_search,
                                                     sample_brand_configs, mock_search_results,
                                                     mock_llm_responses):
        """Test that result structure matches expected JSON schema."""
        brand_config = sample_brand_configs["medical_aesthetics_clinic"]

        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'max_deep_research_iterations': 1,
            'deep_research_iteration_timeout': 300,
            'min_questions_for_research_gap': 2
        }.get(key, default)

        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None

        mock_query_gen = MagicMock()
        mock_query_gen.generate_brand_research_queries.return_value = ["test query"]

        mock_llm = MagicMock()
        mock_llm.adjust_search_terms.return_value = "adjusted_test query"
        mock_llm.synthesize_findings.return_value = mock_llm_responses["synthesis"]
        mock_llm.generate_questions.return_value = []
        mock_llm.execute_prompt.return_value = mock_llm_responses["final_synthesis"]

        mock_execute_web_search.return_value = mock_search_results["pricing_results"]

        engine = DeepResearchEngine(
            llm_client=mock_llm,
            query_generator=mock_query_gen,
            cache_manager=mock_cache,
            config=mock_config
        )

        result = engine.conduct_deep_research(brand_config)

        # Define expected schema structure
        expected_schema = {
            "type": "object",
            "required": ["brand_hash", "brand_config", "iterations", "all_findings",
                        "final_synthesis", "completed_at", "total_iterations"],
            "properties": {
                "brand_hash": {"type": "string", "minLength": 64, "maxLength": 64},
                "brand_config": {"type": "object"},
                "iterations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["iteration", "adjusted_queries", "search_results",
                                   "synthesis", "further_questions", "timestamp"],
                        "properties": {
                            "iteration": {"type": "integer", "minimum": 1},
                            "adjusted_queries": {"type": "array", "items": {"type": "string"}},
                            "search_results": {"type": "array"},
                            "synthesis": {"type": "string"},
                            "further_questions": {"type": "array", "items": {"type": "string"}},
                            "timestamp": {"type": "string"}
                        }
                    }
                },
                "all_findings": {"type": "array"},
                "final_synthesis": {"type": "string", "minLength": 10},
                "completed_at": {"type": "string"},
                "total_iterations": {"type": "integer", "minimum": 0}
            }
        }

        # Basic schema validation (simplified - in real scenario would use jsonschema library)
        assert isinstance(result, dict)
        assert isinstance(result.get('brand_hash'), str)
        assert isinstance(result.get('brand_config'), dict)
        assert isinstance(result.get('iterations'), list)
        assert isinstance(result.get('all_findings'), list)
        assert isinstance(result.get('final_synthesis'), str)
        assert isinstance(result.get('completed_at'), str)
        assert isinstance(result.get('total_iterations'), int)

        # Validate iterations array structure
        for iteration in result['iterations']:
            assert isinstance(iteration.get('iteration'), int)
            assert isinstance(iteration.get('adjusted_queries'), list)
            assert isinstance(iteration.get('search_results'), list)
            assert isinstance(iteration.get('synthesis'), str)
            assert isinstance(iteration.get('further_questions'), list)
            assert isinstance(iteration.get('timestamp'), str)

        # Validate data types and constraints
        assert len(result['brand_hash']) == 64
        assert result['total_iterations'] >= 0
        assert len(result['final_synthesis']) > 0
        assert len(result['iterations']) == result['total_iterations']