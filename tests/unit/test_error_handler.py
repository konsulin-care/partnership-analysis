"""
Unit tests for error_handler.py
"""

from unittest.mock import Mock, patch, call
import pytest
from tenacity import RetryError
from src.python.renderers.error_handler import ErrorHandler


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'carbone_max_retries': 3,
        'carbone_retry_base_delay': 1.0,
        'carbone_retry_max_delay': 10.0
    }.get(key, default)
    return config


@pytest.fixture
def sample_payload():
    """Sample payload for testing."""
    return {
        'data': {'test': 'data'},
        'template': 'test_template',
        'options': {'language': 'en', 'format': 'pdf'}
    }


class TestErrorHandler:
    """Test cases for ErrorHandler class."""

    def test_init(self, mock_config):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler(mock_config)

        assert handler.config == mock_config
        assert handler.max_retries == 3
        assert handler.retry_base_delay == 1.0
        assert handler.retry_max_delay == 10.0

    @patch('src.python.renderers.error_handler.logger')
    def test_execute_with_retry_success(self, mock_logger, mock_config):
        """Test successful function execution with retry."""
        handler = ErrorHandler(mock_config)

        def success_func():
            return "success"

        result = handler.execute_with_retry(success_func)

        assert result == "success"
        mock_logger.debug.assert_has_calls([
            call("Executing function with retry", func_name='success_func'),
            call("Function executed successfully", func_name='success_func')
        ])

    @patch('src.python.renderers.error_handler.logger')
    def test_execute_with_retry_failure_then_success(self, mock_logger, mock_config):
        """Test function execution with retry on failure."""
        handler = ErrorHandler(mock_config)
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = handler.execute_with_retry(failing_func)

        assert result == "success"
        assert call_count == 2
        mock_logger.warning.assert_called_with(
            "Function execution failed, will retry",
            func_name='failing_func',
            error='Temporary failure'
        )

    @patch('src.python.renderers.error_handler.logger')
    def test_execute_with_retry_max_retries_exceeded(self, mock_logger, mock_config):
        """Test function execution fails after max retries."""
        from tenacity import RetryError
        handler = ErrorHandler(mock_config)

        def always_fails():
            raise RuntimeError("Persistent failure")

        with pytest.raises(RetryError) as exc_info:
            handler.execute_with_retry(always_fails)

        # Check that the original exception is wrapped
        assert isinstance(exc_info.value.last_attempt.exception(), RuntimeError)
        assert "Persistent failure" in str(exc_info.value.last_attempt.exception())

    @patch('src.python.renderers.error_handler.logger')
    def test_execute_with_configured_retry_success(self, mock_logger, mock_config):
        """Test successful execution with configured retry."""
        handler = ErrorHandler(mock_config)

        def success_func():
            return "success"

        result = handler.execute_with_configured_retry(success_func)

        assert result == "success"

    @patch('src.python.renderers.error_handler.logger')
    def test_execute_with_configured_retry_with_retry(self, mock_logger, mock_config):
        """Test execution with configured retry on failure."""
        handler = ErrorHandler(mock_config)
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "success"

        result = handler.execute_with_configured_retry(failing_func)

        assert result == "success"
        assert call_count == 2

    @patch('src.python.renderers.error_handler.logger')
    def test_graceful_degradation_success(self, mock_logger, mock_config):
        """Test graceful degradation with successful function."""
        handler = ErrorHandler(mock_config)

        def success_func():
            return "success"

        result = handler.graceful_degradation(success_func)

        assert result == "success"
        mock_logger.debug.assert_has_calls([
            call("Executing function with graceful degradation", func_name='success_func'),
            call("Function executed successfully", func_name='success_func')
        ])

    @patch('src.python.renderers.error_handler.logger')
    def test_graceful_degradation_failure(self, mock_logger, mock_config):
        """Test graceful degradation returns default on failure."""
        handler = ErrorHandler(mock_config)

        def failing_func():
            raise Exception("Function failed")

        result = handler.graceful_degradation(failing_func, default_value="default")

        assert result == "default"
        mock_logger.warning.assert_called_with(
            "Function failed, returning default value",
            func_name='failing_func',
            error='Function failed',
            default='default'
        )

    def test_handle_carbone_error_connection_error(self, mock_config):
        """Test handling ConnectionError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            ConnectionError("Connection failed"), "test operation"
        )

        assert should_retry
        assert "Connection error during test operation" in message

    def test_handle_carbone_error_timeout_error(self, mock_config):
        """Test handling TimeoutError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            TimeoutError("Timeout"), "test operation"
        )

        assert should_retry
        assert "Timeout during test operation" in message

    def test_handle_carbone_error_authentication_error(self, mock_config):
        """Test handling authentication RuntimeError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            RuntimeError("Carbone API key invalid"), "test operation"
        )

        assert not should_retry
        assert "Authentication error" in message

    def test_handle_carbone_error_template_error(self, mock_config):
        """Test handling template RuntimeError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            RuntimeError("Carbone template not found"), "test operation"
        )

        assert not should_retry
        assert "Template error" in message

    def test_handle_carbone_error_payload_error(self, mock_config):
        """Test handling payload RuntimeError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            RuntimeError("Carbone invalid payload"), "test operation"
        )

        assert not should_retry
        assert "Payload error" in message

    def test_handle_carbone_error_generic_runtime_error(self, mock_config):
        """Test handling generic RuntimeError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            RuntimeError("Carbone SDK connection failed"), "test operation"
        )

        assert should_retry
        assert "Carbone SDK error during test operation" in message

    def test_handle_carbone_error_value_error(self, mock_config):
        """Test handling ValueError."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            ValueError("Invalid value"), "test operation"
        )

        assert not should_retry
        assert "Validation error during test operation" in message

    def test_handle_carbone_error_unexpected_error(self, mock_config):
        """Test handling unexpected error type."""
        handler = ErrorHandler(mock_config)

        should_retry, message = handler.handle_carbone_error(
            Exception("Unexpected error"), "test operation"
        )

        assert should_retry
        assert "Unexpected error during test operation" in message

    @patch('src.python.renderers.error_handler.logger')
    def test_attempt_render_with_fallback_success(self, mock_logger, mock_config, sample_payload):
        """Test successful render with fallback."""
        handler = ErrorHandler(mock_config)

        def success_render(payload, output_path):
            return "/path/to/pdf"

        result_success, error_msg, output_path = handler.attempt_render_with_fallback(
            success_render, sample_payload, "/output/path.pdf"
        )

        assert result_success
        assert error_msg == ""
        assert output_path == "/path/to/pdf"

    @patch('src.python.renderers.error_handler.logger')
    def test_attempt_render_with_fallback_failure_no_retry(self, mock_logger, mock_config, sample_payload):
        """Test render failure with non-retryable error."""
        handler = ErrorHandler(mock_config)

        def failing_render(payload, output_path):
            raise ValueError("Invalid payload")

        result_success, error_msg, output_path = handler.attempt_render_with_fallback(
            failing_render, sample_payload, "/output/path.pdf"
        )

        assert not result_success
        assert "Validation error" in error_msg
        assert output_path is None

    @patch('src.python.renderers.error_handler.logger')
    def test_attempt_render_with_fallback_with_retry_success(self, mock_logger, mock_config, sample_payload):
        """Test render failure then retry success."""
        handler = ErrorHandler(mock_config)
        call_count = 0

        def failing_then_success_render(payload, output_path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Temporary failure")
            return "/path/to/pdf"

        result_success, error_msg, output_path = handler.attempt_render_with_fallback(
            failing_then_success_render, sample_payload, "/output/path.pdf"
        )

        assert result_success
        assert error_msg == ""
        assert output_path == "/path/to/pdf"
        assert call_count == 2  # Original call + 1 retry

    @patch('src.python.renderers.error_handler.logger')
    def test_attempt_render_with_fallback_fallback_success(self, mock_logger, mock_config, sample_payload):
        """Test render failure then fallback success."""
        handler = ErrorHandler(mock_config)

        def failing_render(payload, output_path):
            raise ConnectionError("Connection failed")

        def success_render(payload, output_path):
            return "/path/to/fallback.pdf"

        # Mock execute_with_configured_retry to always fail
        with patch.object(handler, 'execute_with_configured_retry', side_effect=ConnectionError("Connection failed")):
            # The fallback will call render_func directly with simplified payload
            result_success, error_msg, output_path = handler.attempt_render_with_fallback(
                success_render, sample_payload, "/output/path.pdf"
            )

            assert result_success
            assert "Rendered with simplified payload" in error_msg
            assert output_path == "/path/to/fallback.pdf"

    @patch('src.python.renderers.error_handler.logger')
    def test_attempt_render_with_fallback_both_fail(self, mock_logger, mock_config, sample_payload):
        """Test both primary and fallback render fail."""
        handler = ErrorHandler(mock_config)

        def failing_render(payload, output_path):
            raise ConnectionError("Connection failed")

        with patch.object(handler, 'execute_with_configured_retry') as mock_retry:
            # Both calls fail
            mock_retry.side_effect = [
                ConnectionError("Connection failed"),
                ValueError("Fallback also failed")
            ]

            result_success, error_msg, output_path = handler.attempt_render_with_fallback(
                failing_render, sample_payload, "/output/path.pdf"
            )

            assert not result_success
            assert "Fallback also failed" in error_msg
            assert output_path is None

    def test_create_fallback_payload(self, mock_config, sample_payload):
        """Test fallback payload creation."""
        handler = ErrorHandler(mock_config)

        fallback = handler._create_fallback_payload(sample_payload)

        assert 'data' in fallback
        assert 'template' in fallback
        assert 'options' in fallback
        assert fallback['data']['document']['title'] == 'Partnership Analysis Report (Simplified)'
        assert 'Report generation encountered issues' in fallback['data']['executive_summary']['headline']
        assert fallback['template'] == sample_payload['template']
        assert fallback['options'] == sample_payload['options']

    @patch('src.python.renderers.error_handler.logger')
    def test_log_error_context(self, mock_logger, mock_config):
        """Test error context logging."""
        handler = ErrorHandler(mock_config)

        error = RuntimeError("Test error")
        context = {'custom_operation': 'test_op', 'payload_size': 100}

        handler.log_error_context('test_operation', error, context)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]['operation'] == 'test_operation'
        assert call_args[1]['error_type'] == 'RuntimeError'
        assert call_args[1]['error_message'] == 'Test error'
        assert call_args[1]['config_max_retries'] == 3
        assert call_args[1]['custom_operation'] == 'test_op'
        assert call_args[1]['payload_size'] == 100