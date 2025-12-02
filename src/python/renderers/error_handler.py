"""
Error Handler Module

Provides robust error handling and recovery for PDF rendering operations,
including retry logic and graceful degradation.
"""

from typing import Any, Callable, Dict, Optional, Tuple
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..config.config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


class ErrorHandler:
    """
    Handles errors and retries for rendering operations.

    This class provides retry logic with exponential backoff for Carbone SDK operations
    and graceful degradation strategies for common failure scenarios.
    """

    def __init__(self, config: ConfigLoader):
        """
        Initialize the error handler with configuration.

        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.max_retries = config.get('carbone_max_retries', 3)
        self.retry_base_delay = config.get('carbone_retry_base_delay', 1.0)
        self.retry_max_delay = config.get('carbone_retry_max_delay', 10.0)

    @retry(
        stop=stop_after_attempt(3),  # Will be overridden by instance config
        wait=wait_exponential(multiplier=1, min=2, max=10),  # Will be overridden
        retry=retry_if_exception_type((ConnectionError, TimeoutError, RuntimeError))
    )
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function execution

        Raises:
            Exception: The last exception encountered after all retries
        """
        try:
            logger.debug("Executing function with retry", func_name=func.__name__)
            result = func(*args, **kwargs)
            logger.debug("Function executed successfully", func_name=func.__name__)
            return result
        except Exception as e:
            logger.warning("Function execution failed, will retry",
                         func_name=func.__name__, error=str(e))
            raise

    def execute_with_configured_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry configuration from config.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function execution

        Raises:
            Exception: The last exception encountered after all retries
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_base_delay,
                                min=self.retry_base_delay,
                                max=self.retry_max_delay),
            retry=retry_if_exception_type((ConnectionError, TimeoutError, RuntimeError))
        )
        def retry_wrapper():
            return func(*args, **kwargs)

        try:
            logger.debug("Executing function with configured retry", func_name=func.__name__)
            result = retry_wrapper()
            logger.debug("Function executed successfully", func_name=func.__name__)
            return result
        except Exception as e:
            logger.warning("Function execution failed after retries",
                         func_name=func.__name__, error=str(e))
            raise

    def graceful_degradation(self, func: Callable, default_value: Any = None, *args, **kwargs) -> Any:
        """
        Execute a function with graceful degradation on failure.

        Args:
            func: Function to execute
            default_value: Value to return on failure
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function or default_value on failure
        """
        try:
            logger.debug("Executing function with graceful degradation", func_name=func.__name__)
            result = func(*args, **kwargs)
            logger.debug("Function executed successfully", func_name=func.__name__)
            return result
        except Exception as e:
            logger.warning("Function failed, returning default value",
                         func_name=func.__name__, error=str(e), default=default_value)
            return default_value

    def handle_carbone_error(self, error: Exception, operation: str) -> Tuple[bool, str]:
        """
        Handle Carbone-specific errors and determine recovery strategy.

        Args:
            error: The exception that occurred
            operation: Description of the operation being performed

        Returns:
            Tuple of (should_retry, error_message)
        """
        error_msg = str(error)
        error_type = type(error).__name__

        # Categorize errors
        if isinstance(error, ConnectionError):
            should_retry = True
            message = f"Connection error during {operation}: {error_msg}"
        elif isinstance(error, TimeoutError):
            should_retry = True
            message = f"Timeout during {operation}: {error_msg}"
        elif isinstance(error, RuntimeError) and "Carbone" in error_msg:
            # Carbone SDK specific errors
            if "API key" in error_msg or "authentication" in error_msg.lower():
                should_retry = False
                message = f"Authentication error: {error_msg}"
            elif "template" in error_msg.lower():
                should_retry = False
                message = f"Template error: {error_msg}"
            elif "payload" in error_msg.lower():
                should_retry = False
                message = f"Payload error: {error_msg}"
            else:
                should_retry = True
                message = f"Carbone SDK error during {operation}: {error_msg}"
        elif isinstance(error, ValueError):
            should_retry = False
            message = f"Validation error during {operation}: {error_msg}"
        else:
            should_retry = True
            message = f"Unexpected error during {operation}: {error_msg}"

        logger.error("Carbone operation failed",
                    operation=operation,
                    error_type=error_type,
                    should_retry=should_retry,
                    message=message)

        return should_retry, message

    def attempt_render_with_fallback(self, render_func: Callable, payload: Dict[str, Any],
                                   output_path: str, *args, **kwargs) -> Tuple[bool, str, Optional[str]]:
        """
        Attempt to render with fallback strategies.

        Args:
            render_func: Rendering function to call
            payload: Payload data
            output_path: Output path for the PDF
            *args: Additional positional arguments for render_func
            **kwargs: Additional keyword arguments for render_func

        Returns:
            Tuple of (success, error_message, output_path_or_none)
        """
        try:
            # First attempt with retry
            result = self.execute_with_configured_retry(render_func, payload, output_path, *args, **kwargs)
            return True, "", result
        except Exception as e:
            should_retry, error_msg = self.handle_carbone_error(e, "PDF rendering")

            if not should_retry:
                # Non-retryable error
                return False, error_msg, None

            # Try one more time with simplified payload if possible
            try:
                logger.info("Attempting fallback rendering with simplified payload")
                simplified_payload = self._create_fallback_payload(payload)
                result = render_func(simplified_payload, output_path, *args, **kwargs)
                logger.warning("Fallback rendering succeeded with simplified payload")
                return True, "Rendered with simplified payload", result
            except Exception as fallback_error:
                _, fallback_msg = self.handle_carbone_error(fallback_error, "fallback rendering")
                return False, f"{error_msg}; Fallback also failed: {fallback_msg}", None

    def _create_fallback_payload(self, original_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a simplified fallback payload for rendering.

        Args:
            original_payload: Original payload that failed

        Returns:
            Simplified payload for fallback rendering
        """
        # Create a minimal payload with just essential information
        fallback = {
            "data": {
                "document": {
                    "title": "Partnership Analysis Report (Simplified)",
                    "date": original_payload.get("data", {}).get("document", {}).get("date", "2025-11-28"),
                    "author": "Analysis System",
                    "contact": "system@example.com"
                },
                "executive_summary": {
                    "headline": "Report generation encountered issues",
                    "key_findings": ["Please check system logs for details"]
                },
                "partnership_overview": {"parties": [], "terms": {}},
                "financial_analysis": {"sections": []},
                "market_research": {"sections": []},
                "recommendations": {"primary": "Contact system administrator", "rationale": "Rendering failed"},
                "references": []
            },
            "template": original_payload.get("template", "partnership_report_v1"),
            "options": original_payload.get("options", {
                "language": "en",
                "format": "pdf",
                "margins": {"top": 20, "bottom": 20, "left": 15, "right": 15}
            })
        }

        logger.debug("Created fallback payload for rendering")
        return fallback

    def log_error_context(self, operation: str, error: Exception,
                         context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log detailed error context for debugging.

        Args:
            operation: Operation that failed
            error: Exception that occurred
            context: Additional context information
        """
        log_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "config_max_retries": self.max_retries,
            "config_retry_delays": f"{self.retry_base_delay}-{self.retry_max_delay}"
        }

        if context:
            log_data.update(context)

        logger.error("Detailed error context", **log_data)