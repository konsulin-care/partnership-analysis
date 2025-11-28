import pytest
from unittest.mock import patch, MagicMock
from src.python.research.research_orchestrator import ResearchOrchestrator
from src.python.research.deep_research_engine import DeepResearchEngine
from src.python.research.llm_client import LLMClient


class TestResearchOrchestrator:
    """Test suite for ResearchOrchestrator class."""

    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    @patch('src.python.research.research_orchestrator.CacheManager')
    def test_init_with_dependencies(self, mock_cache_manager, mock_query_generator, mock_deep_engine, mock_llm_client):
        """Test initialization with provided dependencies."""
        mock_qg = MagicMock()
        mock_cm = MagicMock()
        mock_de = MagicMock()
        mock_llm = MagicMock()

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm, mock_de, mock_llm)

        assert orchestrator.query_generator == mock_qg
        assert orchestrator.cache_manager == mock_cm
        assert orchestrator.deep_research_engine == mock_de
        assert orchestrator.llm_client == mock_llm

    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    @patch('src.python.research.research_orchestrator.CacheManager')
    def test_init_default_dependencies(self, mock_cache_manager, mock_query_generator, mock_deep_engine, mock_llm_client):
        """Test initialization with default dependencies."""
        mock_qg_instance = MagicMock()
        mock_cm_instance = MagicMock()
        mock_de_instance = MagicMock()
        mock_llm_instance = MagicMock()
        mock_query_generator.return_value = mock_qg_instance
        mock_cache_manager.return_value = mock_cm_instance
        mock_deep_engine.return_value = mock_de_instance
        mock_llm_client.return_value = mock_llm_instance

        orchestrator = ResearchOrchestrator()

        mock_query_generator.assert_called_once()
        mock_cache_manager.assert_called_once()
        assert orchestrator.query_generator == mock_qg_instance
        assert orchestrator.cache_manager == mock_cm_instance

    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    def test_deep_research_engine_lazy_instantiation(self, mock_deep_engine):
        """Test that DeepResearchEngine is instantiated lazily when accessed."""
        mock_de_instance = MagicMock()
        mock_deep_engine.return_value = mock_de_instance

        orchestrator = ResearchOrchestrator()

        # Initially not instantiated
        mock_deep_engine.assert_not_called()

        # Access the property
        engine = orchestrator.deep_research_engine

        # Now it should be instantiated
        mock_deep_engine.assert_called_once()
        assert engine == mock_de_instance

    @patch('src.python.research.research_orchestrator.LLMClient')
    def test_llm_client_lazy_instantiation(self, mock_llm_client):
        """Test that LLMClient is instantiated lazily when accessed."""
        mock_llm_instance = MagicMock()
        mock_llm_client.return_value = mock_llm_instance

        orchestrator = ResearchOrchestrator()

        # Initially not instantiated
        mock_llm_client.assert_not_called()

        # Access the property
        client = orchestrator.llm_client

        # Now it should be instantiated
        mock_llm_client.assert_called_once()
        assert client == mock_llm_instance

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.parse_search_results')
    @patch('src.python.research.research_orchestrator.execute_web_search')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_cache_hit_all_queries(self, mock_query_generator, mock_cache_manager,
                                                        mock_deep_engine, mock_llm_client,
                                                        mock_execute_web_search, mock_parse_search_results,
                                                        mock_synthesize):
        """Test orchestrate_research when all queries have cache hits."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["query1", "query2", "query3"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.side_effect = lambda q: f"hash_{q}"
        mock_cm.get_cached_result.return_value = {
            "results": [{"title": "Cached Result", "url": "https://ex.com", "snippet": "Cached", "confidence": 0.8}]
        }
        mock_cache_manager.return_value = mock_cm

        # Mock synthesizer
        mock_synthesize.return_value = {
            "overall": {"average_confidence": 0.9},
            "pricing": {"average": 100}
        }

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("clinic", "medical", "Indonesia")

        # Verify calls
        mock_qg.generate_research_queries.assert_called_once_with("clinic", "medical", "Indonesia")
        assert mock_cm.hash_query.call_count == 3  # once per query
        assert mock_cm.get_cached_result.call_count == 3  # once per query
        mock_execute_web_search.assert_not_called()  # cache hits
        mock_parse_search_results.assert_not_called()  # using cached results
        mock_cm.cache_research_findings.assert_not_called()  # no new caching
        mock_synthesize.assert_called_once()

        # Check result
        assert "pricing" in result
        assert result["overall"]["average_confidence"] == 0.9

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.parse_search_results')
    @patch('src.python.research.research_orchestrator.execute_web_search')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_cache_miss_all_queries(self, mock_query_generator, mock_cache_manager,
                                                         mock_deep_engine, mock_llm_client,
                                                         mock_execute_web_search, mock_parse_search_results,
                                                         mock_synthesize):
        """Test orchestrate_research when all queries miss cache."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["query1", "query2"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.side_effect = lambda q: f"hash_{q}"
        mock_cm.get_cached_result.return_value = None  # cache miss
        mock_cache_manager.return_value = mock_cm

        # Mock web search
        mock_execute_web_search.return_value = [
            {
                "query": "query1",
                "results": [{"title": "Result 1", "url": "https://ex1.com", "snippet": "Snippet 1", "confidence": 0.8}]
            },
            {
                "query": "query2",
                "results": [{"title": "Result 2", "url": "https://ex2.com", "snippet": "Snippet 2", "confidence": 0.7}]
            }
        ]

        # Mock parse results
        mock_parse_search_results.return_value = {
            "parsed_results": [
                {"query": "query1", "title": "Result 1", "url": "https://ex1.com", "snippet": "Snippet 1", "confidence": 0.8}
            ]
        }

        # Mock synthesizer
        mock_synthesize.return_value = {
            "overall": {"average_confidence": 0.75},
            "market_data": {"value": 100}
        }

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("spa", "wellness", "Jakarta")

        # Verify calls
        assert mock_execute_web_search.call_count == 2  # once per query
        assert mock_parse_search_results.call_count == 2  # once per query
        assert mock_cm.cache_research_findings.call_count == 2  # once per query
        mock_synthesize.assert_called_once()

        # Check result
        assert "market_data" in result
        assert result["overall"]["average_confidence"] == 0.75

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.parse_search_results')
    @patch('src.python.research.research_orchestrator.execute_web_search')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_mixed_cache_hits_misses(self, mock_query_generator, mock_cache_manager,
                                                          mock_deep_engine, mock_llm_client,
                                                          mock_execute_web_search, mock_parse_search_results,
                                                          mock_synthesize):
        """Test orchestrate_research with mixed cache hits and misses."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["cached_query", "new_query"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.side_effect = lambda q: f"hash_{q}"
        def mock_get_cached(q_hash):
            if "cached_query" in q_hash:
                return {"results": [{"title": "Cached", "url": "https://cached.com", "snippet": "Cached", "confidence": 0.9}]}
            return None
        mock_cm.get_cached_result.side_effect = mock_get_cached
        mock_cache_manager.return_value = mock_cm

        # Mock web search (only called for new_query)
        mock_execute_web_search.return_value = [
            {
                "query": "new_query",
                "results": [{"title": "New Result", "url": "https://new.com", "snippet": "New", "confidence": 0.6}]
            }
        ]

        # Mock parse results
        mock_parse_search_results.return_value = {
            "parsed_results": [
                {"query": "new_query", "title": "New Result", "url": "https://new.com", "snippet": "New", "confidence": 0.6}
            ]
        }

        # Mock synthesizer
        mock_synthesize.return_value = {
            "overall": {"average_confidence": 0.75},
            "combined": {"count": 2}
        }

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("center", "health", "Bali")

        # Verify calls
        assert mock_execute_web_search.call_count == 1  # only for new_query
        mock_parse_search_results.assert_called_once()
        assert mock_cm.cache_research_findings.call_count == 1  # only for new_query
        mock_synthesize.assert_called_once()

        # Should have findings from both cached and new results
        assert "combined" in result

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_low_confidence_flag(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client, mock_synthesize):
        """Test orchestrate_research flags low confidence data."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["query1"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.return_value = "hash_query1"
        mock_cm.get_cached_result.return_value = {
            "results": [{"title": "Result", "url": "https://ex.com", "snippet": "Snippet", "confidence": 0.5}]
        }
        mock_cache_manager.return_value = mock_cm

        # Mock synthesizer with low confidence
        mock_synthesize.return_value = {
            "overall": {"average_confidence": 0.6},  # below 0.7 threshold
            "data": {"value": 100}
        }

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("test", "test", "test")

        # Should have flags
        assert "flags" in result
        assert "low_confidence_data_detected" in result["flags"]

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_high_confidence_no_flag(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client, mock_synthesize):
        """Test orchestrate_research does not flag high confidence data."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["query1"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.return_value = "hash_query1"
        mock_cm.get_cached_result.return_value = {
            "results": [{"title": "Result", "url": "https://ex.com", "snippet": "Snippet", "confidence": 0.9}]
        }
        mock_cache_manager.return_value = mock_cm

        # Mock synthesizer with high confidence
        mock_synthesize.return_value = {
            "overall": {"average_confidence": 0.8},  # above 0.7 threshold
            "data": {"value": 100}
        }

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("test", "test", "test")

        # Should not have flags
        assert "flags" not in result

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.parse_search_results')
    @patch('src.python.research.research_orchestrator.execute_web_search')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_finding_extraction(self, mock_query_generator, mock_cache_manager,
                                                     mock_deep_engine, mock_llm_client,
                                                     mock_execute_web_search, mock_parse_search_results,
                                                     mock_synthesize):
        """Test that findings are properly extracted from parsed results."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["query1"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.return_value = "hash_query1"
        mock_cm.get_cached_result.return_value = None  # cache miss
        mock_cache_manager.return_value = mock_cm

        # Mock web search and parse
        mock_execute_web_search.return_value = [{
            "query": "query1",
            "results": [{"title": "Test Title", "url": "https://test.com", "snippet": "Test snippet", "confidence": 0.8}]
        }]
        mock_parse_search_results.return_value = {
            "parsed_results": [{
                "query": "query1",
                "title": "Test Title",
                "url": "https://test.com",
                "snippet": "Test snippet",
                "confidence": 0.8
            }]
        }

        # Mock synthesizer
        def mock_synth(findings):
            # Verify the findings structure
            assert len(findings) == 1
            finding = findings[0]
            assert finding["benchmark_type"] == "general"
            assert finding["value"] == "Test snippet"
            assert finding["confidence"] == 0.8
            assert finding["source"] == "https://test.com"
            return {"overall": {"average_confidence": 0.8}}

        mock_synthesize.side_effect = mock_synth

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("test", "test", "test")

        mock_synthesize.assert_called_once()

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_empty_queries(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client, mock_synthesize):
        """Test orchestrate_research with empty query list."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = []
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cache_manager.return_value = mock_cm

        # Mock synthesizer for empty findings
        mock_synthesize.return_value = {
            "overall": {"average_confidence": 0.0}
        }

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("test", "test", "test")

        mock_synthesize.assert_called_once_with([])  # empty findings
        assert result["overall"]["average_confidence"] == 0.0

    @patch('src.python.research.research_orchestrator.synthesize_market_data')
    @patch('src.python.research.research_orchestrator.parse_search_results')
    @patch('src.python.research.research_orchestrator.execute_web_search')
    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_multiple_queries_processing(self, mock_query_generator, mock_cache_manager,
                                                              mock_deep_engine, mock_llm_client,
                                                              mock_execute_web_search, mock_parse_search_results,
                                                              mock_synthesize):
        """Test orchestrate_research processes multiple queries correctly."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["q1", "q2", "q3", "q4"]  # 4 queries
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.side_effect = lambda q: f"hash_{q}"
        mock_cm.get_cached_result.return_value = None  # all cache misses
        mock_cache_manager.return_value = mock_cm

        # Mock web search returns results for all queries
        mock_execute_web_search.return_value = [
            {"query": "q1", "results": [{"title": "R1", "url": "u1", "snippet": "s1", "confidence": 0.8}]},
            {"query": "q2", "results": [{"title": "R2", "url": "u2", "snippet": "s2", "confidence": 0.7}]},
            {"query": "q3", "results": [{"title": "R3", "url": "u3", "snippet": "s3", "confidence": 0.9}]},
            {"query": "q4", "results": [{"title": "R4", "url": "u4", "snippet": "s4", "confidence": 0.6}]}
        ]

        # Mock parse results
        mock_parse_search_results.return_value = {
            "parsed_results": [
                {"query": "q1", "title": "R1", "url": "u1", "snippet": "s1", "confidence": 0.8}
            ]
        }

        # Mock synthesizer
        mock_synthesize.return_value = {"overall": {"average_confidence": 0.75}}

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm)
        result = orchestrator.orchestrate_research("test", "test", "test")

        # Verify multiple calls
        assert mock_cm.hash_query.call_count == 4
        assert mock_cm.get_cached_result.call_count == 4
        assert mock_execute_web_search.call_count == 4  # once per query
        assert mock_parse_search_results.call_count == 4  # once per query
        assert mock_cm.cache_research_findings.call_count == 4  # once per query

        # Should have 4 findings passed to synthesizer
        args = mock_synthesize.call_args[0][0]
        assert len(args) == 4  # 4 findings

    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_deep_mode_success(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client):
        """Test orchestrate_research in deep mode with valid brand_config."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cache_manager.return_value = mock_cm

        mock_de = MagicMock()
        mock_de.conduct_deep_research.return_value = {"deep_result": "success"}
        mock_deep_engine.return_value = mock_de

        brand_config = {"BRAND_NAME": "Test Brand", "BRAND_INDUSTRY": "Test Industry"}

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm, mock_de)
        result = orchestrator.orchestrate_research("clinic", "medical", "Indonesia", research_mode="deep", brand_config=brand_config)

        # Verify deep research engine was called
        mock_de.conduct_deep_research.assert_called_once_with(brand_config)
        assert result == {"deep_result": "success"}

    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_deep_mode_missing_brand_config(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client):
        """Test orchestrate_research in deep mode raises error when brand_config is missing."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cache_manager.return_value = mock_cm

        mock_de = MagicMock()
        mock_deep_engine.return_value = mock_de

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm, mock_de)

        with pytest.raises(ValueError, match="brand_config is required for deep research mode"):
            orchestrator.orchestrate_research("clinic", "medical", "Indonesia", research_mode="deep")

    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_invalid_mode(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client):
        """Test orchestrate_research raises error for invalid research mode."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cache_manager.return_value = mock_cm

        mock_de = MagicMock()
        mock_deep_engine.return_value = mock_de

        orchestrator = ResearchOrchestrator(mock_qg, mock_cm, mock_de)

        with pytest.raises(ValueError, match="Unsupported research mode: invalid"):
            orchestrator.orchestrate_research("clinic", "medical", "Indonesia", research_mode="invalid")

    @patch('src.python.research.research_orchestrator.LLMClient')
    @patch('src.python.research.research_orchestrator.DeepResearchEngine')
    @patch('src.python.research.research_orchestrator.CacheManager')
    @patch('src.python.research.research_orchestrator.QueryGenerator')
    def test_orchestrate_research_backward_compatibility(self, mock_query_generator, mock_cache_manager, mock_deep_engine, mock_llm_client):
        """Test that existing calls without research_mode still work (backward compatibility)."""
        # Setup mocks for basic mode
        mock_qg = MagicMock()
        mock_qg.generate_research_queries.return_value = ["query1"]
        mock_query_generator.return_value = mock_qg

        mock_cm = MagicMock()
        mock_cm.hash_query.return_value = "hash_query1"
        mock_cm.get_cached_result.return_value = {
            "results": [{"title": "Result", "url": "https://ex.com", "snippet": "Snippet", "confidence": 0.8}]
        }
        mock_cache_manager.return_value = mock_cm

        mock_de = MagicMock()
        mock_deep_engine.return_value = mock_de

        with patch('src.python.research.research_orchestrator.synthesize_market_data') as mock_synthesize:
            mock_synthesize.return_value = {"overall": {"average_confidence": 0.8}}

            orchestrator = ResearchOrchestrator(mock_qg, mock_cm, mock_de)
            result = orchestrator.orchestrate_research("clinic", "medical", "Indonesia")  # no research_mode specified

            # Should use basic mode by default
            mock_de.conduct_deep_research.assert_not_called()
            mock_synthesize.assert_called_once()
            assert "overall" in result