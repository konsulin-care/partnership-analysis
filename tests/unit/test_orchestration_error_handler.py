"""
Unit tests for orchestration error_handler.py
"""

from unittest.mock import Mock, patch, call
import pytest
from tenacity import RetryError
from src.python.orchestration.error_handler import OrchestrationErrorHandler
from src.python.config.config_loader import ConfigLoader
from src.python.orchestration.logger import Logger
from src.python.orchestration.state_manager import StateManager

@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock(spec=ConfigLoader)
    config.get.side_effect = lambda key, default=None: {
        'orchestration_max_retries': 3,
        'orchestration_retry_base_delay': 1.0,
        'orchestration_retry_max_delay': 10.0,
        'graceful_degradation_enabled': 'true'
    }.get(key, default)
    return config

@pytest.fixture
def mock_logger():
    """Mock Logger instance."""
    return Mock(spec=Logger)

@pytest.fixture
def mock_state_manager():
    """Mock StateManager instance."""
    return Mock(spec=StateManager)

@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        'execution_id': 'test_execution_123',
        'workflow_name': 'test_workflow',
        'stage_name': 'test_stage',
        'data': {'key': 'value'}
    }

class TestOrchestrationErrorHandler:
    """Test cases for OrchestrationErrorHandler class."""

    def test_init_with_defaults(self, mock_config):
        """Test initialization with default parameters."""
        handler = OrchestrationErrorHandler(mock_config)

        assert handler.config == mock_config
        assert handler.max_retries == 3
        assert handler.retry_base_delay == 1.0
        assert handler.retry_max_delay == 10.0
        assert handler.graceful_degradation_enabled is True
        assert isinstance(handler.logger, Logger)
        assert isinstance(handler.state_manager, StateManager)

    def test_init_with_custom_components(self, mock_config, mock_logger, mock_state_manager):
        """Test initialization with custom logger and state manager."""
        handler = OrchestrationErrorHandler(mock_config, mock_logger, mock_state_manager)

        assert handler.config == mock_config
        assert handler.logger == mock_logger
        assert handler.state_manager == mock_state_manager

    @patch('src.python.orchestration.error_handler.retry')
    def test_execute_with_retry_success(self, mock_retry, mock_config):
        """Test successful function execution with retry."""
        handler = OrchestrationErrorHandler(mock_config)

        def success_func():
            return "success"

        # Mock the retry decorator to call the function directly
        mock_retry.return_value = lambda func: func

        result = handler.execute_with_retry(success_func)

        assert result == "success"

    @patch('src.python.orchestration.error_handler.retry')
    def test_execute_with_retry_failure_then_success(self, mock_retry, mock_config):
        """Test function execution with retry on failure."""
        handler = OrchestrationErrorHandler(mock_config)
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        # Mock the retry decorator to simulate retry behavior
        def mock_retry_decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except ConnectionError:
                    return func(*args, **kwargs)  # Retry once
            return wrapper

        mock_retry.return_value = mock_retry_decorator

        result = handler.execute_with_retry(failing_func)

        assert result == "success"
        assert call_count == 2

    @patch('src.python.orchestration.error_handler.retry')
    def test_execute_with_retry_max_retries_exceeded(self, mock_retry, mock_config):
        """Test function execution fails after max retries."""
        from tenacity import RetryError

        handler = OrchestrationErrorHandler(mock_config)

        def always_fails():
            raise RuntimeError("Persistent failure")

        # Mock the retry decorator to raise RetryError
        mock_retry.side_effect = RetryError(Exception("Max retries exceeded"))

        with pytest.raises(RetryError):
            handler.execute_with_retry(always_fails)

    def test_execute_with_graceful_degradation_success(self, mock_config):
        """Test graceful degradation with successful function."""
        handler = OrchestrationErrorHandler(mock_config)

        def success_func():
            return "success"

        result = handler.execute_with_graceful_degradation(success_func)

        assert result == "success"

    def test_execute_with_graceful_degradation_failure(self, mock_config):
        """Test graceful degradation returns default on failure."""
        handler = OrchestrationErrorHandler(mock_config)

        def failing_func():
            raise Exception("Function failed")

        result = handler.execute_with_graceful_degradation(failing_func, default_value="default")

        assert result == "default"

    def test_handle_workflow_error_retryable(self, mock_config, sample_context):
        """Test handling retryable workflow error."""
        handler = OrchestrationErrorHandler(mock_config)

        error = ConnectionError("Connection failed")
        should_retry, message, recovery_context = handler.handle_workflow_error(
            error, "test_workflow", "test_stage", sample_context
        )

        assert should_retry is True
        assert "Retryable error" in message
        assert recovery_context['retry_strategy'] == 'exponential_backoff'
        assert recovery_context['error_type'] == 'ConnectionError'

    def test_handle_workflow_error_non_retryable(self, mock_config, sample_context):
        """Test handling non-retryable workflow error."""
        handler = OrchestrationErrorHandler(mock_config)

        error = ValueError("Invalid value")
        should_retry, message, recovery_context = handler.handle_workflow_error(
            error, "test_workflow", "test_stage", sample_context
        )

        assert should_retry is False
        assert "Non-retryable error" in message
        assert recovery_context['fallback_strategy'] == 'graceful_degradation'
        assert recovery_context['error_type'] == 'ValueError'

    def test_handle_workflow_error_unexpected(self, mock_config, sample_context):
        """Test handling unexpected workflow error."""
        handler = OrchestrationErrorHandler(mock_config)

        error = Exception("Unexpected error")
        should_retry, message, recovery_context = handler.handle_workflow_error(
            error, "test_workflow", "test_stage", sample_context
        )

        assert should_retry is True
        assert "Unexpected error" in message
        assert recovery_context['retry_strategy'] == 'exponential_backoff'

    def test_get_retry_recovery_context(self, mock_config, sample_context):
        """Test retry recovery context generation."""
        handler = OrchestrationErrorHandler(mock_config)

        error = ConnectionError("Connection failed")
        recovery_context = handler._get_retry_recovery_context(error, sample_context)

        assert recovery_context['retry_strategy'] == 'exponential_backoff'
        assert recovery_context['max_retries'] == 3
        assert recovery_context['error_type'] == 'ConnectionError'
        assert 'retry_timestamp' in recovery_context

    def test_get_fallback_recovery_context(self, mock_config, sample_context):
        """Test fallback recovery context generation."""
        handler = OrchestrationErrorHandler(mock_config)

        error = ValueError("Invalid value")
        recovery_context = handler._get_fallback_recovery_context(error, sample_context)

        assert recovery_context['fallback_strategy'] == 'graceful_degradation'
        assert recovery_context['error_type'] == 'ValueError'
        assert 'fallback_timestamp' in recovery_context

    @patch('src.python.orchestration.error_handler.logger')
    def test_attempt_stage_execution_success(self, mock_logger, mock_config, sample_context):
        """Test successful stage execution."""
        handler = OrchestrationErrorHandler(mock_config)

        def success_stage(context):
            return "stage_result"

        result_success, error_msg, result = handler.attempt_stage_execution(
            success_stage, "test_workflow", "test_stage", sample_context
        )

        assert result_success is True
        assert error_msg == ""
        assert result == "stage_result"

    @patch('src.python.orchestration.error_handler.logger')
    def test_attempt_stage_execution_retryable_failure(self, mock_logger, mock_config, sample_context):
        """Test stage execution with retryable failure."""
        handler = OrchestrationErrorHandler(mock_config)

        def failing_stage(context):
            raise ConnectionError("Connection failed")

        result_success, error_msg, result = handler.attempt_stage_execution(
            failing_stage, "test_workflow", "test_stage", sample_context
        )

        assert result_success is False
        assert "Connection failed" in error_msg
        assert result is None

    @patch('src.python.orchestration.error_handler.logger')
    def test_attempt_stage_execution_non_retryable_failure(self, mock_logger, mock_config, sample_context):
        """Test stage execution with non-retryable failure and graceful degradation."""
        handler = OrchestrationErrorHandler(mock_config)

        def failing_stage(context):
            raise ValueError("Invalid value")

        result_success, error_msg, result = handler.attempt_stage_execution(
            failing_stage, "test_workflow", "test_stage", sample_context
        )

        # Graceful degradation should succeed with default value (None)
        assert result_success is True
        assert "fallback" in error_msg.lower()
        assert result is None

    @patch('src.python.orchestration.error_handler.logger')
    def test_attempt_stage_execution_graceful_degradation(self, mock_logger, mock_config, sample_context):
        """Test stage execution with graceful degradation."""
        handler = OrchestrationErrorHandler(mock_config)

        def failing_stage(context):
            if context.get('fallback_mode'):
                return "fallback_result"
            raise ValueError("Invalid value")

        result_success, error_msg, result = handler.attempt_stage_execution(
            failing_stage, "test_workflow", "test_stage", sample_context
        )

        assert result_success is True
        assert "fallback" in error_msg.lower()
        assert result == "fallback_result"

    def test_execute_fallback_stage(self, mock_config, sample_context):
        """Test fallback stage execution."""
        handler = OrchestrationErrorHandler(mock_config)

        def stage_func(context):
            if context.get('fallback_mode'):
                return "fallback_result"
            raise Exception("Original failed")

        result = handler._execute_fallback_stage(stage_func, sample_context)

        assert result == "fallback_result"

    def test_log_error_metrics(self, mock_config):
        """Test error metrics logging."""
        handler = OrchestrationErrorHandler(mock_config)

        # This should not raise an exception
        handler.log_error_metrics("test_error", "test message", {"key": "value"})

    def test_get_error_recovery_strategy_retryable(self, mock_config):
        """Test recovery strategy for retryable error."""
        handler = OrchestrationErrorHandler(mock_config)

        error = ConnectionError("Connection failed")
        strategy = handler.get_error_recovery_strategy(error)

        assert strategy['strategy'] == 'retry'
        assert strategy['retryable'] is True
        assert strategy['max_attempts'] == 3

    def test_get_error_recovery_strategy_non_retryable(self, mock_config):
        """Test recovery strategy for non-retryable error."""
        handler = OrchestrationErrorHandler(mock_config)

        error = ValueError("Invalid value")
        strategy = handler.get_error_recovery_strategy(error)

        assert strategy['strategy'] == 'graceful_degradation'
        assert strategy['retryable'] is False
        assert strategy['fallback_enabled'] is True

    def test_get_error_recovery_strategy_unexpected(self, mock_config):
        """Test recovery strategy for unexpected error."""
        handler = OrchestrationErrorHandler(mock_config)

        error = Exception("Unexpected error")
        strategy = handler.get_error_recovery_strategy(error)

        assert strategy['strategy'] == 'retry_with_caution'
        assert strategy['retryable'] is True
        assert strategy['max_attempts'] == 2  # More conservative for unknown errors

    def test_graceful_degradation_disabled(self, mock_config):
        """Test behavior when graceful degradation is disabled."""
        mock_config.get.side_effect = lambda key, default=None: {
            'orchestration_max_retries': 3,
            'orchestration_retry_base_delay': 1.0,
            'orchestration_retry_max_delay': 10.0,
            'graceful_degradation_enabled': 'false'
        }.get(key, default)

        handler = OrchestrationErrorHandler(mock_config)

        assert handler.graceful_degradation_enabled is False

        def failing_stage(context):
            raise ValueError("Invalid value")

        result_success, error_msg, result = handler.attempt_stage_execution(
            failing_stage, "test_workflow", "test_stage", {}
        )

        assert result_success is False
        assert "Invalid value" in error_msg
        assert result is None