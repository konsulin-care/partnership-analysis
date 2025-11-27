import pytest
import json
import os
from unittest.mock import mock_open, patch, MagicMock
from datetime import datetime, timezone
from src.python.research.cache_manager import CacheManager, hash_query, get_cached_result, cache_research_findings


class TestCacheManager:
    """Test suite for CacheManager class."""

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_init_with_config(self, mock_config_loader):
        """Test initialization with custom config."""
        mock_config = MagicMock()
        mock_config.get.return_value = '/custom/cache.json'
        mock_config_loader.return_value = mock_config

        with patch('os.path.exists', return_value=False):
            manager = CacheManager(mock_config)

        assert manager.config == mock_config
        assert manager.cache_file_path == '/custom/cache.json'
        mock_config.get.assert_called_with('CACHE_FILE_PATH', './cache/research_cache.json')

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_init_default_config(self, mock_config_loader):
        """Test initialization with default config."""
        mock_config = MagicMock()
        mock_config.get.return_value = './cache/research_cache.json'
        mock_config_loader.return_value = mock_config

        with patch('os.path.exists', return_value=False):
            manager = CacheManager()

        assert manager.config == mock_config
        assert manager.cache_file_path == './cache/research_cache.json'

    @patch('src.python.research.cache_manager.ConfigLoader')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open')
    @patch('json.load', return_value={"test": "data"})
    def test_load_cache_success(self, mock_json_load, mock_open, mock_exists, mock_config_loader):
        """Test successful cache loading."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        cache = manager._load_cache()
        assert cache == {"test": "data"}

    @patch('src.python.research.cache_manager.ConfigLoader')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    def test_load_cache_json_error(self, mock_json_load, mock_file, mock_exists, mock_config_loader):
        """Test cache loading with JSON decode error."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        with patch('builtins.print') as mock_print:
            cache = manager._load_cache()

        # Should return default structure
        assert "cache_version" in cache
        assert "last_updated" in cache
        assert "research_queries" in cache
        assert "extracted_benchmarks" in cache
        mock_print.assert_called_once()

    @patch('src.python.research.cache_manager.ConfigLoader')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', side_effect=IOError("File error"))
    def test_load_cache_io_error(self, mock_file, mock_exists, mock_config_loader):
        """Test cache loading with IO error."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        with patch('builtins.print') as mock_print:
            cache = manager._load_cache()

        # Should return default structure
        assert "cache_version" in cache
        mock_print.assert_called_once()

    @patch('src.python.research.cache_manager.ConfigLoader')
    @patch('os.path.exists', return_value=False)
    def test_load_cache_file_not_exists(self, mock_exists, mock_config_loader):
        """Test cache loading when file doesn't exist."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        cache = manager._load_cache()
        assert "cache_version" in cache
        assert cache["cache_version"] == "1.0"
        assert "research_queries" in cache
        assert "extracted_benchmarks" in cache

    def test_get_default_cache_structure(self):
        """Test default cache structure creation."""
        manager = CacheManager()

        default = manager._get_default_cache_structure()
        assert default["cache_version"] == "1.0"
        assert "last_updated" in default
        assert isinstance(default["last_updated"], str)
        assert default["research_queries"] == {}
        assert default["extracted_benchmarks"] == {}

    @patch('src.python.research.cache_manager.ConfigLoader')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('json.dump')
    @patch('json.load', return_value={"cache_version": "1.0", "last_updated": "2025-11-26T23:50:00Z", "research_queries": {}, "extracted_benchmarks": {}})
    def test_save_cache_success(self, mock_json_load, mock_json_dump, mock_open, mock_makedirs, mock_config_loader):
        """Test successful cache saving."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()
        manager.cache = {"test": "data"}

        with patch('src.python.research.cache_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 26, 23, 50, 0, tzinfo=timezone.utc)
            mock_datetime.timezone.utc = timezone.utc

            manager._save_cache()

        mock_json_dump.assert_called_with({"test": "data", "last_updated": "2025-11-26T23:50:00+00:00"}, mock_open.return_value.__enter__.return_value, indent=2, ensure_ascii=False)

    @patch('src.python.research.cache_manager.ConfigLoader')
    @patch('builtins.open', side_effect=IOError("Write error"))
    def test_save_cache_io_error(self, mock_file, mock_config_loader):
        """Test cache saving with IO error."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        with patch('builtins.print') as mock_print:
            manager._save_cache()

        mock_print.assert_called_once()

    def test_hash_query(self):
        """Test query hashing."""
        manager = CacheManager()
        query = "test query"
        hash_value = manager.hash_query(query)

        # Should be consistent
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex length
        assert hash_value == manager.hash_query(query)  # Same input gives same hash

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_get_cached_result_found_valid(self, mock_config_loader):
        """Test getting cached result when found and valid."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        # Mock cache with valid item
        manager.cache = {
            "research_queries": {
                "hash123": {
                    "cached_at": "2025-11-26T20:00:00Z",
                    "ttl_days": 30,
                    "data": "test"
                }
            }
        }

        with patch('src.python.research.cache_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 26, 21, 0, 0, tzinfo=timezone.utc)
            mock_datetime.fromisoformat.return_value = datetime(2025, 11, 26, 20, 0, 0, tzinfo=timezone.utc)

            result = manager.get_cached_result("hash123", 30)

        assert result == manager.cache["research_queries"]["hash123"]

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_get_cached_result_not_found(self, mock_config_loader):
        """Test getting cached result when not found."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()
        manager.cache = {"research_queries": {}}

        result = manager.get_cached_result("nonexistent")
        assert result is None

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_get_cached_result_expired(self, mock_config_loader):
        """Test getting cached result when expired."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        manager.cache = {
            "research_queries": {
                "hash123": {
                    "cached_at": "2025-11-20T20:00:00Z",  # 6 days ago
                    "ttl_days": 5,
                    "data": "test"
                }
            }
        }

        with patch('src.python.research.cache_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 26, 21, 0, 0, tzinfo=timezone.utc)
            mock_datetime.fromisoformat.return_value = datetime(2025, 11, 20, 20, 0, 0, tzinfo=timezone.utc)

            result = manager.get_cached_result("hash123", 5)

        assert result is not None
        assert result["stale"] is True

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_get_cached_result_invalid_datetime(self, mock_config_loader):
        """Test getting cached result with invalid datetime."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        manager.cache = {
            "research_queries": {
                "hash123": {
                    "cached_at": "invalid-date",
                    "ttl_days": 30
                }
            }
        }

        result = manager.get_cached_result("hash123")
        assert result is None

    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_get_cached_result_no_cached_at(self, mock_config_loader):
        """Test getting cached result with missing cached_at."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        manager.cache = {
            "research_queries": {
                "hash123": {
                    "ttl_days": 30
                }
            }
        }

        result = manager.get_cached_result("hash123")
        assert result is None

    @patch('src.python.research.cache_manager.CacheManager._save_cache')
    @patch('src.python.research.cache_manager.ConfigLoader')
    def test_cache_research_findings(self, mock_config_loader, mock_save):
        """Test caching research findings."""
        mock_config_loader.return_value = MagicMock()
        manager = CacheManager()

        findings = {
            "query": "test query",
            "results": [{"title": "test"}],
            "synthesis": "test synthesis"
        }

        with patch('src.python.research.cache_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 26, 23, 50, 0, tzinfo=timezone.utc)

            manager.cache_research_findings("hash123", findings, 30)

        assert "research_queries" in manager.cache
        assert "hash123" in manager.cache["research_queries"]
        cached_item = manager.cache["research_queries"]["hash123"]
        assert cached_item["query"] == "test query"
        assert cached_item["cached_at"] == "2025-11-26T23:50:00+00:00"
        assert cached_item["ttl_days"] == 30
        assert cached_item["results"] == [{"title": "test"}]
        assert cached_item["synthesis"] == "test synthesis"
        mock_save.assert_called_once()

    @patch('src.python.research.cache_manager.CacheManager')
    def test_hash_query_convenience_function(self, mock_cache_manager_class):
        """Test hash_query convenience function."""
        mock_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_manager
        mock_manager.hash_query.return_value = "mocked_hash"

        result = hash_query("test query")

        mock_cache_manager_class.assert_called_once()
        mock_manager.hash_query.assert_called_with("test query")
        assert result == "mocked_hash"

    @patch('src.python.research.cache_manager.CacheManager')
    def test_get_cached_result_convenience_function(self, mock_cache_manager_class):
        """Test get_cached_result convenience function."""
        mock_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_manager
        mock_manager.get_cached_result.return_value = {"cached": "data"}

        result = get_cached_result("hash123", 30)

        mock_cache_manager_class.assert_called_once()
        mock_manager.get_cached_result.assert_called_with("hash123", 30)
        assert result == {"cached": "data"}

    @patch('src.python.research.cache_manager.CacheManager')
    def test_cache_research_findings_convenience_function(self, mock_cache_manager_class):
        """Test cache_research_findings convenience function."""
        mock_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_manager

        findings = {"query": "test"}
        cache_research_findings("hash123", findings, 30)

        mock_cache_manager_class.assert_called_once()
        mock_manager.cache_research_findings.assert_called_with("hash123", findings, 30)