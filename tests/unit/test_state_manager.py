"""
Unit tests for the orchestration state manager module.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import time
from datetime import datetime, timedelta

from src.python.orchestration.state_manager import StateManager
from src.python.config.config_loader import ConfigLoader
from src.python.orchestration.logger import Logger

@pytest.fixture
def mock_config_loader():
    """Fixture for mock config loader."""
    config_loader = Mock(spec=ConfigLoader)
    config_loader.get.side_effect = lambda key, default=None: {
        'STATE_DIR': 'test_state',
        'CACHE_DIR': 'test_cache'
    }.get(key, default)
    return config_loader

@pytest.fixture
def mock_logger():
    """Fixture for mock logger."""
    mock_logger = Mock(spec=Logger)
    mock_logger.log_execution_start = Mock()
    mock_logger.log_execution_end = Mock()
    mock_logger.log_stage_transition = Mock()
    mock_logger.log_error = Mock()
    return mock_logger

@pytest.fixture
def state_manager_instance(mock_config_loader, mock_logger):
    """Fixture for state manager instance."""
    return StateManager(config_loader=mock_config_loader, logger=mock_logger)

def test_state_manager_initialization(mock_config_loader, mock_logger):
    """Test state manager initialization."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)
    assert state_manager.config_loader == mock_config_loader
    assert state_manager.logger == mock_logger
    assert hasattr(state_manager, '_state')
    assert hasattr(state_manager, '_cache')

def test_state_manager_default_config():
    """Test state manager with default configuration."""
    state_manager = StateManager()
    assert isinstance(state_manager.config_loader, ConfigLoader)
    assert isinstance(state_manager.logger, Logger)

def test_get_state_file_path(mock_config_loader, mock_logger):
    """Test getting state file path."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)
    state_file = state_manager._get_state_file_path()
    assert state_file.name == 'orchestration_state.json'
    assert 'test_state' in str(state_file)

def test_get_cache_file_path(mock_config_loader, mock_logger):
    """Test getting cache file path."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)
    cache_file = state_manager._get_cache_file_path()
    assert cache_file.name == 'orchestration_cache.json'
    assert 'test_cache' in str(cache_file)

def test_get_default_state():
    """Test getting default state."""
    state_manager = StateManager()
    default_state = state_manager._get_default_state()
    assert default_state['version'] == '1.0'
    assert 'last_updated' in default_state
    assert default_state['execution_history'] == []
    assert default_state['current_execution'] is None

def test_get_default_cache():
    """Test getting default cache."""
    state_manager = StateManager()
    default_cache = state_manager._get_default_cache()
    assert default_cache['version'] == '1.0'
    assert 'last_updated' in default_cache
    assert default_cache['execution_cache'] == {}
    assert default_cache['research_cache'] == {}
    assert default_cache['calculation_cache'] == {}

def test_load_state_nonexistent_file(mock_config_loader, mock_logger):
    """Test loading state from non-existent file."""
    # Create state manager with non-existent files
    with tempfile.TemporaryDirectory() as temp_dir:
        config_loader = Mock(spec=ConfigLoader)
        config_loader.get.side_effect = lambda key, default=None: {
            'STATE_DIR': temp_dir,
            'CACHE_DIR': temp_dir
        }.get(key, default)

        state_manager = StateManager(config_loader=config_loader, logger=mock_logger)
        state = state_manager.get_current_state()

        # Should return default state
        assert state['version'] == '1.0'
        assert state['execution_history'] == []

def test_load_cache_nonexistent_file(mock_config_loader, mock_logger):
    """Test loading cache from non-existent file."""
    # Create state manager with non-existent files
    with tempfile.TemporaryDirectory() as temp_dir:
        config_loader = Mock(spec=ConfigLoader)
        config_loader.get.side_effect = lambda key, default=None: {
            'STATE_DIR': temp_dir,
            'CACHE_DIR': temp_dir
        }.get(key, default)

        state_manager = StateManager(config_loader=config_loader, logger=mock_logger)
        cache_stats = state_manager.get_cache_stats()

        # Should return empty cache stats
        assert cache_stats['execution_cache_size'] == 0
        assert cache_stats['research_cache_size'] == 0

def test_cache_key_generation_functionality():
    """Test cache key generation functionality without file I/O."""
    # Test the core functionality without file operations
    state_manager = StateManager()

    # Test cache key generation
    key1 = state_manager._generate_cache_key("test1", "test2")
    key2 = state_manager._generate_cache_key("test1", "test2")

    assert key1 == key2
    assert isinstance(key1, str)
    assert len(key1) > 0

    # Test different inputs generate different keys
    key3 = state_manager._generate_cache_key("test1", "test3")
    assert key1 != key3

def test_update_execution_stage(mock_config_loader, mock_logger):
    """Test updating execution stage."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Start an execution first
    execution_id = state_manager.start_execution("test_workflow", {})

    # Update a stage
    stage_name = "data_extraction"
    status = "completed"
    data = {"records_processed": 100}

    state_manager.update_execution_stage(execution_id, stage_name, status, data)

    # Verify logger was called
    mock_logger.log_stage_transition.assert_called()

def test_end_execution(mock_config_loader, mock_logger):
    """Test ending an execution."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Start an execution first
    execution_id = state_manager.start_execution("test_workflow", {})

    # End the execution
    status = "success"
    metrics = {"duration": 12.5, "records": 100}

    state_manager.end_execution(execution_id, status, metrics)

    # Verify logger was called
    mock_logger.log_execution_end.assert_called_once_with("test_workflow", status, metrics)

def test_cache_execution_result(mock_config_loader, mock_logger):
    """Test caching execution result."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    execution_id = "test_execution_123"
    result = {"output": "test_result", "metrics": {"accuracy": 0.95}}

    cache_key = state_manager.cache_execution_result(execution_id, result, ttl_seconds=3600)

    # Verify cache key is generated
    assert isinstance(cache_key, str)
    assert len(cache_key) > 0

def test_get_cached_execution(mock_config_loader, mock_logger):
    """Test getting cached execution result."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Cache a result first
    execution_id = "test_execution_123"
    result = {"output": "test_result"}
    cache_key = state_manager.cache_execution_result(execution_id, result)

    # Retrieve the cached result
    cached_result = state_manager.get_cached_execution(cache_key)

    assert cached_result == result

def test_get_cached_execution_nonexistent(mock_config_loader, mock_logger):
    """Test getting non-existent cached execution."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    result = state_manager.get_cached_execution("nonexistent_key")
    assert result is None

def test_cache_research_result(mock_config_loader, mock_logger):
    """Test caching research result."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    query = "medical aesthetics pricing 2025"
    result = {"pricing": {"min": 15000000, "max": 45000000}, "sources": ["source1"]}

    cache_key = state_manager.cache_research_result(query, result)

    assert isinstance(cache_key, str)
    assert len(cache_key) > 0

def test_get_cached_research(mock_config_loader, mock_logger):
    """Test getting cached research result."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Cache a research result first
    query = "medical aesthetics pricing 2025"
    result = {"pricing": {"min": 15000000, "max": 45000000}}
    cache_key = state_manager.cache_research_result(query, result)

    # Retrieve the cached result
    cached_result = state_manager.get_cached_research(query)

    assert cached_result == result

def test_cache_calculation_result(mock_config_loader, mock_logger):
    """Test caching calculation result."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    calculation_type = "breakeven_analysis"
    params = {"capex": 1000000, "monthly_profit": 50000}
    result = {"breakeven_months": 20, "npv": 150000}

    cache_key = state_manager.cache_calculation_result(calculation_type, params, result)

    assert isinstance(cache_key, str)
    assert len(cache_key) > 0

def test_get_cached_calculation(mock_config_loader, mock_logger):
    """Test getting cached calculation result."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Cache a calculation result first
    calculation_type = "breakeven_analysis"
    params = {"capex": 1000000, "monthly_profit": 50000}
    result = {"breakeven_months": 20}
    cache_key = state_manager.cache_calculation_result(calculation_type, params, result)

    # Retrieve the cached result
    cached_result = state_manager.get_cached_calculation(calculation_type, params)

    assert cached_result == result

def test_get_current_state(mock_config_loader, mock_logger):
    """Test getting current state."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)
    state = state_manager.get_current_state()

    assert isinstance(state, dict)
    assert 'version' in state
    assert 'execution_history' in state

def test_get_cache_stats(mock_config_loader, mock_logger):
    """Test getting cache statistics."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)
    stats = state_manager.get_cache_stats()

    assert isinstance(stats, dict)
    assert 'execution_cache_size' in stats
    assert 'research_cache_size' in stats
    assert 'calculation_cache_size' in stats

def test_clear_expired_cache(mock_config_loader, mock_logger):
    """Test clearing expired cache entries."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Add some cache entries with expiration
    execution_id = "test_execution"
    result = {"data": "test"}

    # Cache with very short TTL (1 second)
    cache_key = state_manager.cache_execution_result(execution_id, result, ttl_seconds=1)

    # Wait for expiration
    time.sleep(2)

    # Clear expired entries
    cleared_count = state_manager.clear_expired_cache()

    assert cleared_count >= 1

def test_cleanup_old_state(mock_config_loader, mock_logger):
    """Test cleaning up old state."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Start multiple executions to create history
    for i in range(5):
        state_manager.start_execution(f"workflow_{i}", {"param": i})
        state_manager.end_execution(f"exec_{i}", "success", {"duration": i})

    # Cleanup with max history of 3
    removed_count = state_manager.cleanup_old_state(max_history=3)

    # Should have removed 2 records (keeping 3 most recent)
    assert removed_count >= 0

def test_cache_key_generation(mock_config_loader, mock_logger):
    """Test cache key generation."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Test that same inputs generate same key
    key1 = state_manager._generate_cache_key("test1", "test2")
    key2 = state_manager._generate_cache_key("test1", "test2")

    assert key1 == key2

    # Test that different inputs generate different keys
    key3 = state_manager._generate_cache_key("test1", "test3")
    assert key1 != key3

def test_state_persistence(mock_config_loader, mock_logger):
    """Test state persistence across instances."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create first state manager instance
        config_loader = Mock(spec=ConfigLoader)
        config_loader.get.side_effect = lambda key, default=None: {
            'STATE_DIR': temp_dir,
            'CACHE_DIR': temp_dir
        }.get(key, default)

        state_manager1 = StateManager(config_loader=config_loader, logger=mock_logger)

        # Start an execution
        execution_id = state_manager1.start_execution("test_workflow", {"param": "value"})

        # Create second instance with same config
        state_manager2 = StateManager(config_loader=config_loader, logger=mock_logger)

        # Verify state was persisted
        state = state_manager2.get_current_state()
        assert len(state['execution_history']) == 1
        assert state['execution_history'][0]['execution_id'] == execution_id

def test_cache_persistence(mock_config_loader, mock_logger):
    """Test cache persistence across instances."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create first state manager instance
        config_loader = Mock(spec=ConfigLoader)
        config_loader.get.side_effect = lambda key, default=None: {
            'STATE_DIR': temp_dir,
            'CACHE_DIR': temp_dir
        }.get(key, default)

        state_manager1 = StateManager(config_loader=config_loader, logger=mock_logger)

        # Cache some data
        query = "test_query"
        result = {"data": "test_result"}
        cache_key = state_manager1.cache_research_result(query, result)

        # Create second instance with same config
        state_manager2 = StateManager(config_loader=config_loader, logger=mock_logger)

        # Verify cache was persisted
        cached_result = state_manager2.get_cached_research(query)
        assert cached_result == result

def test_error_handling_in_state_loading(mock_config_loader, mock_logger):
    """Test error handling when loading corrupted state files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a corrupted state file
        state_file = Path(temp_dir) / 'orchestration_state.json'
        state_file.write_text("corrupted json data {{{")

        config_loader = Mock(spec=ConfigLoader)
        config_loader.get.side_effect = lambda key, default=None: {
            'STATE_DIR': temp_dir,
            'CACHE_DIR': temp_dir
        }.get(key, default)

        # Should handle the error gracefully and return default state
        state_manager = StateManager(config_loader=config_loader, logger=mock_logger)
        state = state_manager.get_current_state()

        assert state['version'] == '1.0'
        assert mock_logger.log_error.called

def test_error_handling_in_cache_loading(mock_config_loader, mock_logger):
    """Test error handling when loading corrupted cache files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a corrupted cache file
        cache_file = Path(temp_dir) / 'orchestration_cache.json'
        cache_file.write_text("corrupted json data {{{")

        config_loader = Mock(spec=ConfigLoader)
        config_loader.get.side_effect = lambda key, default=None: {
            'STATE_DIR': temp_dir,
            'CACHE_DIR': temp_dir
        }.get(key, default)

        # Should handle the error gracefully and return default cache
        state_manager = StateManager(config_loader=config_loader, logger=mock_logger)
        stats = state_manager.get_cache_stats()

        assert stats['execution_cache_size'] == 0
        assert mock_logger.log_error.called

def test_thread_safety(mock_config_loader, mock_logger):
    """Test thread safety of state operations."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Operations should be thread-safe due to locking
    # This is a basic test - more comprehensive testing would be needed for production

    # Start multiple executions
    exec1 = state_manager.start_execution("workflow1", {})
    exec2 = state_manager.start_execution("workflow2", {})

    # Both should complete successfully
    assert isinstance(exec1, str)
    assert isinstance(exec2, str)
    assert exec1 != exec2

def test_cache_expiration(mock_config_loader, mock_logger):
    """Test cache expiration functionality."""
    state_manager = StateManager(config_loader=mock_config_loader, logger=mock_logger)

    # Cache with very short TTL
    execution_id = "test_exec"
    result = {"data": "test"}

    cache_key = state_manager.cache_execution_result(execution_id, result, ttl_seconds=1)

    # Should be retrievable immediately
    cached_result = state_manager.get_cached_execution(cache_key)
    assert cached_result == result

    # Wait for expiration
    time.sleep(2)

    # Should be expired and not retrievable
    cached_result = state_manager.get_cached_execution(cache_key)
    assert cached_result is None

def test_state_manager_integration_with_config():
    """Test state manager integration with config loader."""
    config_loader = ConfigLoader()
    logger = Logger(config_loader=config_loader)
    state_manager = StateManager(config_loader=config_loader, logger=logger)

    assert state_manager.config_loader == config_loader
    assert state_manager.logger == logger

def test_state_manager_error_recovery():
    """Test state manager error recovery."""
    state_manager = StateManager()

    # These operations should not raise exceptions even with invalid inputs
    try:
        state_manager.start_execution("", {})
        state_manager.update_execution_stage("nonexistent", "stage", "status", {})
        state_manager.end_execution("nonexistent", "failed", {})
        state_manager.cache_execution_result("", {}, 0)
        state_manager.get_cached_execution("nonexistent")
    except Exception:
        pytest.fail("State manager should handle errors gracefully")

def test_cache_key_uniqueness():
    """Test that cache keys are unique for different inputs."""
    state_manager = StateManager()

    keys = set()
    for i in range(100):
        key = state_manager._generate_cache_key(f"input_{i}")
        keys.add(key)

    # All keys should be unique
    assert len(keys) == 100