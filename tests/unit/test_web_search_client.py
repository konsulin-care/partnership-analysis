import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.python.research.web_search_client import execute_web_search, _is_cache_valid, _perform_search


class TestWebSearchClient:
    """Test suite for web search client functions."""

    @patch('src.python.research.web_search_client.hashlib.sha256')
    @patch('src.python.research.web_search_client.ConfigLoader')
    @patch('src.python.research.web_search_client.genai')
    @patch('src.python.research.web_search_client.datetime')
    def test_execute_web_search_cache_hit(self, mock_datetime, mock_genai, mock_config_loader, mock_sha256):
        """Test execute_web_search with cache hit."""
        # Mock hash
        mock_sha = MagicMock()
        mock_sha.hexdigest.return_value = "hash123"
        mock_sha256.return_value = mock_sha

        # Mock config
        mock_config = MagicMock()
        mock_config.get.return_value = "test_api_key"
        mock_config_loader.return_value = mock_config

        # Mock cache with valid cached result
        cache = {
            "research_queries": {
                "hash123": {
                    "cached_at": "2025-11-26T20:00:00Z",
                    "ttl_days": 30,
                    "query": "test query",
                    "results": [{"title": "cached result"}],
                    "synthesis": "cached synthesis"
                }
            }
        }

        # Mock datetime for cache validation
        mock_datetime.now.return_value = datetime(2025, 11, 26, 21, 0, 0, tzinfo=timezone.utc)
        mock_datetime.fromisoformat.return_value = datetime(2025, 11, 26, 20, 0, 0, tzinfo=timezone.utc)

        queries = ["test query"]
        results = execute_web_search(queries, cache)

        assert len(results) == 1
        assert results[0]["query"] == "test query"
        assert results[0]["results"] == [{"title": "cached result"}]
        # ConfigLoader is called to get api_key, but genai.Client is not called since cache hit
        # Note: ConfigLoader creates the client internally, but for cache hit, search is not performed

    @patch('src.python.research.web_search_client.hashlib.sha256')
    @patch('src.python.research.web_search_client.ConfigLoader')
    @patch('src.python.research.web_search_client.genai')
    @patch('src.python.research.web_search_client.datetime')
    @patch('src.python.research.web_search_client._perform_search')
    def test_execute_web_search_cache_miss(self, mock_perform_search, mock_datetime, mock_genai, mock_config_loader, mock_sha256):
        """Test execute_web_search with cache miss."""
        # Mock hash
        mock_sha = MagicMock()
        mock_sha.hexdigest.return_value = "hash123"
        mock_sha256.return_value = mock_sha

        # Mock config
        mock_config = MagicMock()
        mock_config.get.return_value = "test_api_key"
        mock_config_loader.return_value = mock_config

        # Mock genai
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # Mock cache miss
        cache = {"research_queries": {}}

        # Mock datetime
        mock_datetime.now.return_value = datetime(2025, 11, 26, 23, 50, 0, tzinfo=timezone.utc)

        # Mock search results
        mock_perform_search.return_value = [
            {"title": "search result 1", "url": "http://example.com", "snippet": "snippet 1", "confidence": 0.8}
        ]

        queries = ["new query"]
        results = execute_web_search(queries, cache)

        assert len(results) == 1
        assert results[0]["query"] == "new query"
        assert results[0]["results"] == [
            {"title": "search result 1", "url": "http://example.com", "snippet": "snippet 1", "confidence": 0.8}
        ]
        assert results[0]["cached_at"] == "2025-11-26T23:50:00+00:00"
        assert results[0]["ttl_days"] == 30

        # Should have called genai
        mock_genai.Client.assert_called_once_with(api_key="test_api_key")
        mock_perform_search.assert_called_once()

        # Should have cached the result
        assert "research_queries" in cache
        assert "hash123" in cache["research_queries"]  # hash of "new query"

    @patch('src.python.research.web_search_client.ConfigLoader')
    def test_execute_web_search_no_api_key(self, mock_config_loader):
        """Test execute_web_search with missing API key."""
        mock_config = MagicMock()
        mock_config.get.return_value = None
        mock_config_loader.return_value = mock_config

        cache = {}
        queries = ["test"]

        with pytest.raises(ValueError, match="Google GenAI API key not configured"):
            execute_web_search(queries, cache)

    @patch('src.python.research.web_search_client.datetime')
    def test_is_cache_valid_valid(self, mock_datetime):
        """Test _is_cache_valid with valid cache."""
        cached = {
            "cached_at": "2025-11-26T20:00:00Z",
            "ttl_days": 30
        }

        mock_datetime.now.return_value = datetime(2025, 11, 26, 21, 0, 0, tzinfo=timezone.utc)
        mock_datetime.fromisoformat.return_value = datetime(2025, 11, 26, 20, 0, 0, tzinfo=timezone.utc)

        assert _is_cache_valid(cached) is True

    @patch('src.python.research.web_search_client.datetime')
    def test_is_cache_valid_expired(self, mock_datetime):
        """Test _is_cache_valid with expired cache."""
        cached = {
            "cached_at": "2025-11-20T20:00:00Z",
            "ttl_days": 5
        }

        mock_datetime.now.return_value = datetime(2025, 11, 26, 21, 0, 0, tzinfo=timezone.utc)
        mock_datetime.fromisoformat.return_value = datetime(2025, 11, 20, 20, 0, 0, tzinfo=timezone.utc)

        assert _is_cache_valid(cached) is False

    def test_is_cache_valid_no_cached_at(self):
        """Test _is_cache_valid with missing cached_at."""
        cached = {"ttl_days": 30}
        assert _is_cache_valid(cached) is False

    def test_is_cache_valid_invalid_datetime(self):
        """Test _is_cache_valid with invalid datetime."""
        cached = {
            "cached_at": "invalid-date",
            "ttl_days": 30
        }
        assert _is_cache_valid(cached) is False

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_success(self, mock_genai):
        """Test _perform_search successful response."""
        # Mock the client
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models

        # Mock response with function call
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_function_response = MagicMock()
        mock_function_response.response = {
            'results': [
                {
                    'title': 'Test Title',
                    'url': 'https://example.com',
                    'snippet': 'Test snippet'
                }
            ]
        }
        mock_part.function_response = mock_function_response
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_models.generate_content.return_value = mock_response

        # Mock config
        mock_config = MagicMock()

        results = _perform_search(mock_client, mock_config, "test query")

        assert len(results) == 1
        assert results[0]['title'] == 'Test Title'
        assert results[0]['url'] == 'https://example.com'
        assert results[0]['snippet'] == 'Test snippet'
        assert results[0]['confidence'] == 0.85

        mock_models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="Search the web for: test query",
            config=mock_config
        )

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_no_candidates(self, mock_genai):
        """Test _perform_search with no candidates in response."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_models.generate_content.return_value = mock_response

        results = _perform_search(mock_client, MagicMock(), "test query")

        assert results == []

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_no_parts(self, mock_genai):
        """Test _perform_search with candidate but no parts."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_candidate = MagicMock()
        mock_candidate.content = None
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_models.generate_content.return_value = mock_response

        results = _perform_search(mock_client, MagicMock(), "test query")

        assert results == []

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_no_function_response(self, mock_genai):
        """Test _perform_search with part but no function response."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.function_response = None
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_models.generate_content.return_value = mock_response

        results = _perform_search(mock_client, MagicMock(), "test query")

        assert results == []

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_no_results_in_response(self, mock_genai):
        """Test _perform_search with function response but no results."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_function_response = MagicMock()
        mock_function_response.response = {}
        mock_part.function_response = mock_function_response
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_models.generate_content.return_value = mock_response

        results = _perform_search(mock_client, MagicMock(), "test query")

        assert results == []

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_retry_on_failure(self, mock_genai):
        """Test _perform_search with retry on failure."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_models.generate_content.side_effect = [Exception("API Error"), MagicMock()]  # Fail then succeed

        # For the successful call
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_function_response = MagicMock()
        mock_function_response.response = {'results': []}
        mock_part.function_response = mock_function_response
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_models.generate_content.side_effect = [Exception("API Error"), mock_response]

        results = _perform_search(mock_client, MagicMock(), "test query")

        assert results == []
        assert mock_models.generate_content.call_count == 2  # One failure, one success

    @patch('src.python.research.web_search_client.genai')
    def test_perform_search_max_retries_exceeded(self, mock_genai):
        """Test _perform_search when max retries exceeded."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_models.generate_content.side_effect = Exception("Persistent API Error")

        with pytest.raises(Exception):
            _perform_search(mock_client, MagicMock(), "test query")

        # Should have tried 3 times (initial + 2 retries)
        assert mock_models.generate_content.call_count == 3
