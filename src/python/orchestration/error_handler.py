"""
Orchestration Error Handler Module

Provides robust error handling and recovery for orchestration workflow operations,
including retry logic, graceful degradation, and workflow-specific error handling.
"""

from typing import Any, Callable, Dict, Optional, Tuple, List
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime
import traceback

from src.python.config.config_loader import ConfigLoader
from src.python.orchestration.logger import Logger
from src.python.orchestration.state_manager import StateManager

logger = structlog.get_logger(__name__)

class OrchestrationErrorHandler:
    """
    Handles errors and retries for orchestration workflow operations.

    This class provides retry logic with exponential backoff for orchestration operations,
    graceful degradation strategies, and workflow-specific error handling.
    """

    def __init__(self, config: ConfigLoader, logger: Optional[Logger] = None,
                 state_manager: Optional[StateManager] = None):
        """
        Initialize the orchestration error handler with configuration.

        Args:
            config: Configuration loader instance
            logger: Optional Logger instance for structured logging
            state_manager: Optional StateManager instance for state tracking
        """
        self.config = config
        self.logger = logger or Logger(config)
        self.state_manager = state_manager or StateManager(config, self.logger)

        # Configuration parameters
        self.max_retries = config.get('orchestration_max_retries', 3)
        self.retry_base_delay = config.get('orchestration_retry_base_delay', 1.0)
        self.retry_max_delay = config.get('orchestration_retry_max_delay', 10.0)
        self.graceful_degradation_enabled = config.get('graceful_degradation_enabled', 'true').lower() == 'true'

        # Error categorization
        self.retryable_errors = (ConnectionError, TimeoutError, RuntimeError)
        self.non_retryable_errors = (ValueError, TypeError, KeyError)

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic using default configuration.

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
            retry=retry_if_exception_type(self.retryable_errors)
        )
        def retry_wrapper():
            try:
                self.logger.get_logger("orchestration").debug(
                    "Executing function with retry",
                    func_name=func.__name__
                )
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.get_logger("orchestration").warning(
                    "Function execution failed, will retry",
                    func_name=func.__name__,
                    error=str(e)
                )
                raise

        return retry_wrapper()

    def execute_with_graceful_degradation(self, func: Callable, default_value: Any = None,
                                         *args, **kwargs) -> Any:
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
            self.logger.get_logger("orchestration").debug(
                "Executing function with graceful degradation",
                func_name=func.__name__
            )
            result = func(*args, **kwargs)
            self.logger.get_logger("orchestration").debug(
                "Function executed successfully",
                func_name=func.__name__
            )
            return result
        except Exception as e:
            self.logger.get_logger("orchestration").warning(
                "Function failed, returning default value",
                func_name=func.__name__,
                error=str(e),
                default=default_value
            )
            return default_value

    def handle_workflow_error(self, error: Exception, workflow_name: str, stage_name: str,
                            context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Handle workflow-specific errors and determine recovery strategy.

        Args:
            error: The exception that occurred
            workflow_name: Name of the workflow
            stage_name: Name of the stage where error occurred
            context: Additional context about the error

        Returns:
            Tuple of (should_retry, error_message, recovery_context)
        """
        error_msg = str(error)
        error_type = type(error).__name__

        # Categorize errors and determine recovery strategy
        if isinstance(error, self.retryable_errors):
            should_retry = True
            message = f"Retryable error in {workflow_name} stage {stage_name}: {error_msg}"
            recovery_context = self._get_retry_recovery_context(error, context)
        elif isinstance(error, self.non_retryable_errors):
            should_retry = False
            message = f"Non-retryable error in {workflow_name} stage {stage_name}: {error_msg}"
            recovery_context = self._get_fallback_recovery_context(error, context)
        else:
            should_retry = True
            message = f"Unexpected error in {workflow_name} stage {stage_name}: {error_msg}"
            recovery_context = self._get_retry_recovery_context(error, context)

        # Log the error with full context
        self._log_workflow_error(workflow_name, stage_name, error, message, context)

        return should_retry, message, recovery_context

    def _get_retry_recovery_context(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recovery context for retryable errors.

        Args:
            error: The exception that occurred
            context: Original context data

        Returns:
            Recovery context for retry
        """
        recovery_context = context.copy()
        recovery_context.update({
            'retry_strategy': 'exponential_backoff',
            'max_retries': self.max_retries,
            'retry_delay_base': self.retry_base_delay,
            'retry_delay_max': self.retry_max_delay,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'retry_timestamp': datetime.utcnow().isoformat()
        })
        return recovery_context

    def _get_fallback_recovery_context(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recovery context for non-retryable errors.

        Args:
            error: The exception that occurred
            context: Original context data

        Returns:
            Recovery context for fallback
        """
        recovery_context = context.copy()
        recovery_context.update({
            'fallback_strategy': 'graceful_degradation',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'fallback_timestamp': datetime.utcnow().isoformat(),
            'graceful_degradation_enabled': self.graceful_degradation_enabled
        })
        return recovery_context

    def _log_workflow_error(self, workflow_name: str, stage_name: str, error: Exception,
                          message: str, context: Dict[str, Any]) -> None:
        """
        Log detailed workflow error information.

        Args:
            workflow_name: Name of the workflow
            stage_name: Name of the stage
            error: The exception that occurred
            message: Error message
            context: Additional context information
        """
        log_data = {
            'workflow_name': workflow_name,
            'stage_name': stage_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_traceback': traceback.format_exc(),
            'message': message,
            'config_max_retries': self.max_retries,
            'config_retry_delays': f"{self.retry_base_delay}-{self.retry_max_delay}",
            'graceful_degradation_enabled': self.graceful_degradation_enabled,
            'timestamp': datetime.utcnow().isoformat()
        }

        if context:
            log_data.update(context)

        self.logger.get_logger("orchestration").error("workflow_error", **log_data)

        # Also log to state manager for execution tracking
        if self.state_manager:
            self.state_manager.update_execution_stage(
                context.get('execution_id', 'unknown'),
                stage_name,
                'failed',
                {
                    'error_type': type(error).__name__,
                    'error_message': str(error),
                    'recovery_strategy': 'retry' if isinstance(error, self.retryable_errors) else 'fallback',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

    def attempt_stage_execution(self, stage_func: Callable, workflow_name: str, stage_name: str,
                               context: Dict[str, Any]) -> Tuple[bool, str, Any]:
        """
        Attempt to execute a workflow stage with comprehensive error handling.

        Args:
            stage_func: Stage function to execute
            workflow_name: Name of the workflow
            stage_name: Name of the stage
            context: Context data for the stage

        Returns:
            Tuple of (success, error_message, result_or_none)
        """
        try:
            # First attempt with retry
            result = self.execute_with_retry(stage_func, context)
            return True, "", result
        except Exception as e:
            should_retry, error_msg, recovery_context = self.handle_workflow_error(
                e, workflow_name, stage_name, context
            )

            if not should_retry:
                # Non-retryable error - attempt graceful degradation if enabled
                if self.graceful_degradation_enabled:
                    try:
                        self.logger.get_logger("orchestration").info(
                            "Attempting graceful degradation for stage",
                            workflow_name=workflow_name,
                            stage_name=stage_name
                        )
                        fallback_result = self._execute_fallback_stage(stage_func, context)
                        return True, f"Stage completed with fallback: {error_msg}", fallback_result
                    except Exception as fallback_error:
                        self.logger.get_logger("orchestration").error(
                            "Fallback execution also failed",
                            workflow_name=workflow_name,
                            stage_name=stage_name,
                            fallback_error=str(fallback_error)
                        )
                        return False, f"{error_msg}; Fallback failed: {str(fallback_error)}", None
                else:
                    return False, error_msg, None

            # Retryable error - attempt one more retry with updated context
            try:
                self.logger.get_logger("orchestration").info(
                    "Attempting retry with updated context",
                    workflow_name=workflow_name,
                    stage_name=stage_name
                )
                retry_result = stage_func(recovery_context)
                return True, "Stage completed after retry", retry_result
            except Exception as retry_error:
                self.logger.get_logger("orchestration").error(
                    "Retry also failed",
                    workflow_name=workflow_name,
                    stage_name=stage_name,
                    retry_error=str(retry_error)
                )
                return False, f"{error_msg}; Retry failed: {str(retry_error)}", None

    def _execute_fallback_stage(self, stage_func: Callable, context: Dict[str, Any]) -> Any:
        """
        Execute a fallback version of a stage function.

        Args:
            stage_func: Original stage function
            context: Context data for the stage

        Returns:
            Result of fallback execution
        """
        # Create a simplified context for fallback execution
        fallback_context = context.copy()
        fallback_context['fallback_mode'] = True
        fallback_context['fallback_timestamp'] = datetime.utcnow().isoformat()

        # Execute with graceful degradation
        return self.execute_with_graceful_degradation(stage_func, None, fallback_context)

    def log_error_metrics(self, error_type: str, error_message: str,
                         context: Dict[str, Any]) -> None:
        """
        Log error metrics for monitoring and analysis.

        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context information
        """
        metrics_data = {
            'error_type': error_type,
            'error_message': error_message,
            'severity': 'error',
            'component': 'orchestration'
        }

        if context:
            metrics_data.update(context)

        self.logger.log_metric("error_occurred", error_message, metrics_data)

    def get_error_recovery_strategy(self, error: Exception) -> Dict[str, Any]:
        """
        Get the appropriate recovery strategy for a given error.

        Args:
            error: The exception that occurred

        Returns:
            Dictionary containing recovery strategy details
        """
        error_type = type(error).__name__
        error_message = str(error)

        if isinstance(error, self.retryable_errors):
            return {
                'strategy': 'retry',
                'max_attempts': self.max_retries,
                'delay_pattern': 'exponential_backoff',
                'base_delay': self.retry_base_delay,
                'max_delay': self.retry_max_delay,
                'retryable': True
            }
        elif isinstance(error, self.non_retryable_errors):
            return {
                'strategy': 'graceful_degradation',
                'fallback_enabled': self.graceful_degradation_enabled,
                'default_behavior': 'continue_with_defaults',
                'retryable': False
            }
        else:
            return {
                'strategy': 'retry_with_caution',
                'max_attempts': min(self.max_retries, 2),  # More conservative for unknown errors
                'delay_pattern': 'exponential_backoff',
                'base_delay': self.retry_base_delay,
                'max_delay': self.retry_max_delay,
                'retryable': True
            }