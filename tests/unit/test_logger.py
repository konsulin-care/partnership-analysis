"""
Unit tests for the orchestration logger module.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import logging
import structlog
from datetime import datetime

from src.python.orchestration.logger import Logger
from src.python.config.config_loader import ConfigLoader

@pytest.fixture
def mock_config_loader():
    """Fixture for mock config loader."""
    config_loader = Mock(spec=ConfigLoader)
    config_loader.get.side_effect = lambda key, default=None: {
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': None,
        'LOG_JSON_FORMAT': 'false',
        'LOG_DIR': 'logs'
    }.get(key, default)
    return config_loader

@pytest.fixture
def logger_instance(mock_config_loader):
    """Fixture for logger instance."""
    return Logger(config_loader=mock_config_loader)

def test_logger_initialization(mock_config_loader):
    """Test logger initialization."""
    logger = Logger(config_loader=mock_config_loader)
    assert logger.config_loader == mock_config_loader
    assert hasattr(logger, 'get_logger')

def test_logger_default_config():
    """Test logger with default configuration."""
    logger = Logger()
    assert isinstance(logger.config_loader, ConfigLoader)
    assert hasattr(logger, 'get_logger')

def test_get_logger(logger_instance):
    """Test getting a named logger."""
    logger = logger_instance.get_logger("test_module")
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'debug')

def test_log_execution_start(logger_instance, capsys):
    """Test logging execution start."""
    workflow_name = "test_workflow"
    context = {"param1": "value1", "param2": 42}

    # Mock the logger to capture the call
    with patch.object(logger_instance, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger_instance.log_execution_start(workflow_name, context)

        # Verify the call
        mock_get_logger.assert_called_once_with("orchestration")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[1]
        assert call_args['workflow_name'] == workflow_name
        assert call_args['param1'] == context['param1']
        assert call_args['param2'] == context['param2']
        assert 'timestamp' in call_args

def test_log_execution_end(logger_instance):
    """Test logging execution end."""
    workflow_name = "test_workflow"
    status = "success"
    metrics = {"duration": 12.5, "records_processed": 100}

    with patch.object(logger_instance, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger_instance.log_execution_end(workflow_name, status, metrics)

        mock_get_logger.assert_called_once_with("orchestration")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[1]
        assert call_args['workflow_name'] == workflow_name
        assert call_args['status'] == status
        assert call_args['duration'] == metrics['duration']

def test_log_stage_transition(logger_instance):
    """Test logging stage transition."""
    workflow_name = "test_workflow"
    from_stage = "stage1"
    to_stage = "stage2"
    data_context = {"records": 50}

    with patch.object(logger_instance, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger_instance.log_stage_transition(workflow_name, from_stage, to_stage, data_context)

        mock_get_logger.assert_called_once_with("orchestration")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[1]
        assert call_args['workflow_name'] == workflow_name
        assert call_args['from_stage'] == from_stage
        assert call_args['to_stage'] == to_stage

def test_log_error(logger_instance):
    """Test logging error."""
    error_type = "validation_error"
    message = "Invalid input data"
    context = {"field": "revenue", "value": -100}

    with patch.object(logger_instance, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger_instance.log_error(error_type, message, context)

        mock_get_logger.assert_called_once_with("orchestration")
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[1]
        assert call_args['error_type'] == error_type
        assert call_args['message'] == message
        assert call_args['field'] == context['field']

def test_log_error_with_warning_severity(logger_instance):
    """Test logging error with warning severity."""
    with patch.object(logger_instance, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger_instance.log_error("data_quality", "Low confidence data", {}, severity="warning")

        mock_logger.warning.assert_called_once()

def test_log_metric(logger_instance):
    """Test logging metric."""
    metric_name = "processing_time"
    value = 42.7
    context = {"stage": "data_extraction"}

    with patch.object(logger_instance, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger_instance.log_metric(metric_name, value, context)

        mock_get_logger.assert_called_once_with("orchestration")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[1]
        assert call_args['metric_name'] == metric_name
        assert call_args['value'] == value

def test_add_context(logger_instance):
    """Test adding context to logger."""
    # This is a bit tricky to test directly, but we can verify it doesn't raise errors
    logger_instance.add_context(workflow_id="test_123", iteration=1)
    # Context should be added without error

def test_clear_context(logger_instance):
    """Test clearing context."""
    # Should not raise errors
    logger_instance.clear_context()

def test_get_log_config(mock_config_loader):
    """Test getting log configuration."""
    logger = Logger(config_loader=mock_config_loader)
    config = logger._get_log_config()

    assert config['log_level'] == 'INFO'
    assert config['json_format'] == False
    assert config['log_dir'] == 'logs'

def test_get_log_config_json_format():
    """Test getting log configuration with JSON format enabled."""
    config_loader = Mock(spec=ConfigLoader)
    config_loader.get.side_effect = lambda key, default=None: {
        'LOG_LEVEL': 'DEBUG',
        'LOG_JSON_FORMAT': 'true',
        'LOG_DIR': 'logs'
    }.get(key, default)

    logger = Logger(config_loader=config_loader)
    config = logger._get_log_config()

    assert config['log_level'] == 'DEBUG'
    assert config['json_format'] == True

@patch('src.python.orchestration.logger.structlog.configure')
@patch('src.python.orchestration.logger.logging.basicConfig')
def test_configure_logging(mock_basic_config, mock_structlog_configure, mock_config_loader):
    """Test logging configuration."""
    logger = Logger(config_loader=mock_config_loader)

    # Verify structlog was configured
    mock_structlog_configure.assert_called_once()
    mock_basic_config.assert_called_once()

@patch('src.python.orchestration.logger.Path.mkdir')
def test_log_dir_creation(mock_mkdir, mock_config_loader):
    """Test log directory creation."""
    config_loader = Mock(spec=ConfigLoader)
    config_loader.get.side_effect = lambda key, default=None: {
        'LOG_DIR': '/tmp/test_logs'
    }.get(key, default)

    logger = Logger(config_loader=config_loader)
    mock_mkdir.assert_called_once_with(exist_ok=True)

def test_logger_integration_with_structlog():
    """Test that logger integrates properly with structlog."""
    logger = Logger()

    # Get a logger instance
    test_logger = logger.get_logger("test_integration")

    # Verify it has the expected methods
    assert hasattr(test_logger, 'info')
    assert hasattr(test_logger, 'debug')
    assert hasattr(test_logger, 'warning')
    assert hasattr(test_logger, 'error')
    assert hasattr(test_logger, 'critical')

def test_logger_context_management():
    """Test logger context management."""
    logger = Logger()

    # Test adding and clearing context
    logger.add_context(test_key="test_value")
    logger.clear_context()

    # Should not raise any errors

def test_logger_error_handling():
    """Test logger error handling."""
    logger = Logger()

    # These should not raise exceptions even with invalid inputs
    logger.log_error("test_error", "test message", {})
    logger.log_error("test_error", "test message", {"key": "value"})
    logger.log_metric("test_metric", 123, {})
    logger.log_execution_start("test_workflow", {})
    logger.log_execution_end("test_workflow", "success", {})
    logger.log_stage_transition("workflow", "stage1", "stage2", {})

def test_logger_timestamp_generation():
    """Test that timestamps are generated correctly."""
    logger = Logger()

    with patch.object(logger, 'get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger.log_execution_start("test", {})

        # Verify timestamp is in the call
        call_args = mock_logger.info.call_args[1]
        assert 'timestamp' in call_args

        # Verify it's a valid ISO format timestamp
        timestamp_str = call_args['timestamp']
        try:
            datetime.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")