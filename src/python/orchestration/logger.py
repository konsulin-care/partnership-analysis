"""
Structured logging module for the orchestration layer.

This module provides structured logging capabilities using structlog
and integrates with the configuration system for log levels and output formats.
"""

import logging
import sys
from typing import Dict, Any, Optional
import structlog
from datetime import datetime
import json
from pathlib import Path

from src.python.config.config_loader import ConfigLoader

class Logger:
    """
    Structured logger for the orchestration layer.

    Provides consistent logging across all orchestration components
    with support for JSON and console output formats.
    """

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """
        Initialize the logger with configuration.

        Args:
            config_loader: ConfigLoader instance for logging configuration
                          If None, uses default configuration
        """
        self.config_loader = config_loader or ConfigLoader()
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure structlog with appropriate processors and formatters."""
        # Get logging configuration from config
        log_config = self._get_log_config()

        # Create shared processors
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        # Add JSON formatter if enabled
        if log_config.get('json_format', False):
            shared_processors.append(structlog.processors.JSONRenderer())
        else:
            shared_processors.append(structlog.dev.ConsoleRenderer())

        # Configure structlog
        structlog.configure(
            processors=shared_processors,
            wrapper_class=structlog.make_filtering_bound_logger(log_config['log_level']),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=False
        )

        # Configure standard logging
        logging.basicConfig(
            level=log_config['log_level'],
            format='%(message)s',
            stream=sys.stdout,
            force=True
        )

    def _get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration from environment or use defaults."""
        config = {
            'log_level': self.config_loader.get('LOG_LEVEL', 'INFO'),
            'log_file': self.config_loader.get('LOG_FILE', None),
            'json_format': self.config_loader.get('LOG_JSON_FORMAT', 'false').lower() == 'true',
            'log_dir': self.config_loader.get('LOG_DIR', 'logs')
        }

        # Ensure log directory exists
        log_dir = Path(config['log_dir'])
        log_dir.mkdir(exist_ok=True)

        return config

    def get_logger(self, name: str) -> structlog.BoundLogger:
        """
        Get a named logger instance.

        Args:
            name: Name of the logger (typically module name)

        Returns:
            Configured structlog logger instance
        """
        return structlog.get_logger(name)

    def log_execution_start(self, workflow_name: str, context: Dict[str, Any]) -> None:
        """
        Log the start of a workflow execution.

        Args:
            workflow_name: Name of the workflow being started
            context: Additional context data for the execution
        """
        logger = self.get_logger("orchestration")
        # Remove workflow_name from context if present to avoid duplicate key error
        log_context = context.copy()
        log_context.pop('workflow_name', None)
        log_context.pop('timestamp', None)  # Also remove timestamp if present

        logger.info("workflow_started",
                   workflow_name=workflow_name,
                   timestamp=datetime.utcnow().isoformat(),
                   **log_context)

    def log_execution_end(self, workflow_name: str, status: str, metrics: Dict[str, Any]) -> None:
        """
        Log the end of a workflow execution.

        Args:
            workflow_name: Name of the workflow that ended
            status: Status of execution (success, partial_success, failed)
            metrics: Execution metrics and results
        """
        logger = self.get_logger("orchestration")
        # Remove conflicting keys from metrics to avoid duplicate key errors
        log_metrics = metrics.copy()
        log_metrics.pop('workflow_name', None)
        log_metrics.pop('status', None)
        log_metrics.pop('timestamp', None)

        logger.info("workflow_completed",
                   workflow_name=workflow_name,
                   status=status,
                   timestamp=datetime.utcnow().isoformat(),
                   **log_metrics)

    def log_stage_transition(self, workflow_name: str, from_stage: str, to_stage: str,
                           data_context: Dict[str, Any]) -> None:
        """
        Log transition between workflow stages.

        Args:
            workflow_name: Name of the workflow
            from_stage: Stage being transitioned from
            to_stage: Stage being transitioned to
            data_context: Context data about the transition
        """
        logger = self.get_logger("orchestration")
        # Remove conflicting keys from data_context to avoid duplicate key errors
        log_context = data_context.copy()
        log_context.pop('workflow_name', None)
        log_context.pop('from_stage', None)
        log_context.pop('to_stage', None)
        log_context.pop('timestamp', None)

        logger.info("stage_transition",
                   workflow_name=workflow_name,
                   from_stage=from_stage,
                   to_stage=to_stage,
                   timestamp=datetime.utcnow().isoformat(),
                   **log_context)

    def log_error(self, error_type: str, message: str, context: Dict[str, Any],
                 severity: str = "error") -> None:
        """
        Log an error with structured context.

        Args:
            error_type: Type/category of error
            message: Error message
            context: Additional context about the error
            severity: Severity level (error, warning, critical)
        """
        logger = self.get_logger("orchestration")
        log_method = getattr(logger, severity.lower())

        # Remove conflicting keys from context to avoid duplicate key errors
        log_context = context.copy()
        log_context.pop('error_type', None)
        log_context.pop('message', None)
        log_context.pop('timestamp', None)

        log_method("execution_error",
                  error_type=error_type,
                  message=message,
                  timestamp=datetime.utcnow().isoformat(),
                  **log_context)

    def log_metric(self, metric_name: str, value: Any, context: Dict[str, Any]) -> None:
        """
        Log a performance or business metric.

        Args:
            metric_name: Name of the metric
            value: Value of the metric
            context: Additional context for the metric
        """
        logger = self.get_logger("orchestration")
        # Remove conflicting keys from context to avoid duplicate key errors
        log_context = context.copy()
        log_context.pop('metric_name', None)
        log_context.pop('value', None)
        log_context.pop('timestamp', None)

        logger.info("metric_recorded",
                   metric_name=metric_name,
                   value=value,
                   timestamp=datetime.utcnow().isoformat(),
                   **log_context)

    def add_context(self, **kwargs: Any) -> None:
        """
        Add context variables to the current logging context.

        Args:
            **kwargs: Key-value pairs to add to context
        """
        structlog.contextvars.bind_contextvars(**kwargs)

    def clear_context(self) -> None:
        """Clear the current logging context."""
        structlog.contextvars.clear_contextvars()