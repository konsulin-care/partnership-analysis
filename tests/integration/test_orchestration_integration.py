"""
Integration tests for orchestration components.

Tests the interaction between error_handler, workflow_coordinator, logger, and state_manager.
"""

from unittest.mock import Mock, patch
import pytest
from src.python.orchestration.workflow_coordinator import WorkflowCoordinator, WorkflowStage
from src.python.orchestration.error_handler import OrchestrationErrorHandler
from src.python.config.config_loader import ConfigLoader
from src.python.orchestration.logger import Logger
from src.python.orchestration.state_manager import StateManager

@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance with comprehensive configuration."""
    config = Mock(spec=ConfigLoader)
    config.get.side_effect = lambda key, default=None: {
        'workflow_name': 'partnership_analysis',
        'max_concurrent_stages': 1,
        'enable_parallel_execution': 'false',
        'orchestration_max_retries': 3,
        'orchestration_retry_base_delay': 1.0,
        'orchestration_retry_max_delay': 10.0,
        'graceful_degradation_enabled': 'true',
        'LOG_LEVEL': 'INFO',
        'LOG_JSON_FORMAT': 'false',
        'STATE_DIR': 'state',
        'CACHE_DIR': 'cache'
    }.get(key, default)
    return config

@pytest.fixture
def sample_workflow_stages():
    """Sample workflow stages for integration testing."""
    def research_stage(context):
        return {
            'research_results': ['market_data_1', 'market_data_2'],
            'sources': ['source_1', 'source_2']
        }

    def extraction_stage(context):
        previous_results = context.get('stage_research_stage_result', {})
        return {
            'extracted_data': previous_results.get('research_results', []),
            'benchmarks': [100.0, 200.0, 300.0]
        }

    def calculation_stage(context):
        extracted_data = context.get('stage_extraction_stage_result', {})
        return {
            'calculated_metrics': {
                'total': len(extracted_data.get('extracted_data', [])),
                'average': sum(extracted_data.get('benchmarks', [])) / len(extracted_data.get('benchmarks', [1]))
            }
        }

    def formatting_stage(context):
        calculation_results = context.get('stage_calculation_stage_result', {})
        return {
            'formatted_output': f"Results: {calculation_results.get('calculated_metrics', {})}"
        }

    return [
        WorkflowStage("research_stage", research_stage, "Perform market research", True, True),
        WorkflowStage("extraction_stage", extraction_stage, "Extract data from research", True, True),
        WorkflowStage("calculation_stage", calculation_stage, "Calculate financial metrics", True, True),
        WorkflowStage("formatting_stage", formatting_stage, "Format final output", False, True)
    ]

class TestOrchestrationIntegration:
    """Integration tests for orchestration components."""

    def test_full_workflow_execution_success(self, mock_config, sample_workflow_stages):
        """Test complete workflow execution with all stages succeeding."""
        # Create coordinator with real components
        coordinator = WorkflowCoordinator(mock_config)

        # Add all stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # Initialize execution
        execution_id = coordinator.initialize_execution({
            'partner_name': 'Test Partner',
            'industry': 'Medical Aesthetics',
            'location': 'Indonesia'
        })

        assert execution_id is not None
        assert coordinator.execution_id == execution_id

        # Execute workflow
        success, error_msg, final_context = coordinator.execute_workflow()

        # Verify successful execution
        assert success is True
        assert error_msg == ""
        assert final_context['stages_completed'] == 4  # All stages completed
        assert final_context['stages_failed'] == 0

        # Verify stage results are in context
        assert 'stage_research_stage_result' in final_context
        assert 'stage_extraction_stage_result' in final_context
        assert 'stage_calculation_stage_result' in final_context
        assert 'stage_formatting_stage_result' in final_context

        # Verify data flow between stages
        research_result = final_context['stage_research_stage_result']
        extraction_result = final_context['stage_extraction_stage_result']

        assert extraction_result['extracted_data'] == research_result['research_results']

    def test_workflow_with_stage_failure_recovery(self, mock_config, sample_workflow_stages):
        """Test workflow execution with stage failure and recovery."""
        # Create coordinator with real components
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages, but modify the extraction stage to fail initially then succeed
        def failing_then_success_extraction(context):
            if not context.get('retry_attempt'):
                raise ConnectionError("Temporary network failure")
            # On retry, succeed
            previous_results = context.get('stage_research_stage_result', {})
            return {
                'extracted_data': previous_results.get('research_results', []),
                'benchmarks': [100.0, 200.0, 300.0],
                'recovered': True
            }

        extraction_stage = WorkflowStage(
            "extraction_stage",
            failing_then_success_extraction,
            "Extract data from research",
            True,
            True
        )

        # Add stages
        coordinator.add_stage(sample_workflow_stages[0])  # research
        coordinator.add_stage(extraction_stage)  # modified extraction
        coordinator.add_stage(sample_workflow_stages[2])  # calculation
        coordinator.add_stage(sample_workflow_stages[3])  # formatting

        # Execute workflow with error recovery (includes initialization)
        success, error_msg, final_context = coordinator.execute_with_error_recovery(
            {'partner_name': 'Test Partner', 'retry_attempt': False},
            max_retries=2
        )

        # Should succeed because the retry mechanism should handle the temporary failure
        assert success is True
        assert final_context['stages_completed'] == 4
        assert final_context['stages_failed'] == 0

        # Verify the extraction stage result shows recovery
        extraction_result = final_context['stage_extraction_stage_result']
        assert extraction_result.get('recovered') is True

    def test_workflow_with_non_retryable_failure(self, mock_config, sample_workflow_stages):
        """Test workflow execution with non-retryable stage failure."""
        # Create coordinator with real components
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages, but modify the calculation stage to fail with non-retryable error
        def failing_calculation(context):
            raise ValueError("Invalid calculation parameters")

        calculation_stage = WorkflowStage(
            "calculation_stage",
            failing_calculation,
            "Calculate financial metrics",
            True,  # Required stage
            False  # Non-retryable
        )

        # Add stages
        coordinator.add_stage(sample_workflow_stages[0])  # research
        coordinator.add_stage(sample_workflow_stages[1])  # extraction
        coordinator.add_stage(calculation_stage)  # failing calculation
        coordinator.add_stage(sample_workflow_stages[3])  # formatting

        # Initialize execution
        coordinator.initialize_execution({
            'partner_name': 'Test Partner'
        })

        # Execute workflow with error recovery
        success, error_msg, final_context = coordinator.execute_with_error_recovery(
            {'partner_name': 'Test Partner', 'retry_attempt': False},
            max_retries=2
        )

        # Should succeed because graceful degradation handles the non-retryable error
        assert success is True
        assert error_msg == ""  # No error message when graceful degradation succeeds
        assert final_context['stages_completed'] == 3  # All stages completed (calculation with graceful degradation)
        assert final_context['stages_failed'] == 1  # Formatting stage failed

    def test_workflow_with_optional_stage_failure(self, mock_config, sample_workflow_stages):
        """Test workflow execution with optional stage failure."""
        # Create coordinator with real components
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages, but modify the formatting stage (optional) to fail
        def failing_formatting(context):
            raise RuntimeError("Formatting service unavailable")

        formatting_stage = WorkflowStage(
            "formatting_stage",
            failing_formatting,
            "Format final output",
            False,  # Optional stage
            True
        )

        # Add stages
        coordinator.add_stage(sample_workflow_stages[0])  # research
        coordinator.add_stage(sample_workflow_stages[1])  # extraction
        coordinator.add_stage(sample_workflow_stages[2])  # calculation
        coordinator.add_stage(formatting_stage)  # failing formatting

        # Initialize execution
        coordinator.initialize_execution({
            'partner_name': 'Test Partner'
        })

        # Execute workflow with error recovery
        success, error_msg, final_context = coordinator.execute_with_error_recovery(
            {'partner_name': 'Test Partner', 'retry_attempt': False},
            max_retries=2
        )

        # Should succeed because optional stage failure is allowed
        assert success is True
        assert final_context['stages_completed'] == 3  # First three stages completed
        assert final_context['stages_failed'] == 1  # Optional formatting stage failed

    def test_error_handler_integration(self, mock_config):
        """Test error handler integration with workflow coordinator."""
        # Create error handler
        error_handler = OrchestrationErrorHandler(mock_config)

        # Test retryable error handling
        def failing_func():
            raise ConnectionError("Network timeout")

        should_retry, message, recovery_context = error_handler.handle_workflow_error(
            ConnectionError("Network timeout"),
            "test_workflow",
            "test_stage",
            {'execution_id': 'test_123'}
        )

        assert should_retry is True
        assert "Retryable error" in message
        assert recovery_context['retry_strategy'] == 'exponential_backoff'

        # Test non-retryable error handling
        should_retry, message, recovery_context = error_handler.handle_workflow_error(
            ValueError("Invalid input"),
            "test_workflow",
            "test_stage",
            {'execution_id': 'test_123'}
        )

        assert should_retry is False
        assert "Non-retryable error" in message
        assert recovery_context['fallback_strategy'] == 'graceful_degradation'

    def test_workflow_state_management(self, mock_config, sample_workflow_stages):
        """Test state management integration."""
        # Create coordinator
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # Initialize execution
        execution_id = coordinator.initialize_execution({
            'partner_name': 'Test Partner'
        })

        # Verify state manager was used
        assert execution_id is not None
        assert coordinator.state_manager is not None

        # Get current state
        current_state = coordinator.get_current_state()
        assert current_state['execution_id'] == execution_id
        assert current_state['workflow_name'] == 'partnership_analysis'
        assert current_state['total_stages'] == 4

        # Execute workflow
        success, error_msg, final_context = coordinator.execute_workflow()

        # Verify final state
        assert success is True
        assert final_context['execution_id'] == execution_id
        assert 'end_time' in final_context
        assert 'duration_seconds' in final_context

    def test_workflow_logging_integration(self, mock_config, sample_workflow_stages):
        """Test logging integration."""
        # Create coordinator
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # Initialize execution
        execution_id = coordinator.initialize_execution({
            'partner_name': 'Test Partner'
        })

        # Verify logger was used
        assert coordinator.logger is not None

        # Execute workflow
        success, error_msg, final_context = coordinator.execute_workflow()

        # Verify successful execution
        assert success is True

    def test_workflow_with_graceful_degradation(self, mock_config):
        """Test workflow with graceful degradation enabled."""
        # Create coordinator
        coordinator = WorkflowCoordinator(mock_config)

        def research_stage(context):
            return {'research_results': ['data1', 'data2']}

        def failing_extraction(context):
            raise ValueError("Cannot extract data from research")

        def calculation_stage(context):
            # This should still run even if extraction fails
            return {'calculated_metrics': {'total': 0}}

        # Add stages
        coordinator.add_stage(WorkflowStage("research", research_stage, "Research", True, True))
        coordinator.add_stage(WorkflowStage("extraction", failing_extraction, "Extraction", False, True))  # Optional
        coordinator.add_stage(WorkflowStage("calculation", calculation_stage, "Calculation", True, True))

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Execute workflow
        success, error_msg, final_context = coordinator.execute_workflow()

        # Should succeed because extraction is optional
        assert success is True
        assert final_context['stages_completed'] == 3  # research, extraction (with graceful degradation), and calculation
        assert final_context['stages_failed'] == 0  # extraction handled gracefully

    def test_workflow_configuration_validation(self, mock_config, sample_workflow_stages):
        """Test workflow configuration validation."""
        coordinator = WorkflowCoordinator(mock_config)

        # Add valid stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # Validate configuration
        is_valid, error_msg = coordinator.validate_workflow_configuration()

        assert is_valid is True
        assert error_msg == "Workflow configuration is valid"

        # Test invalid configuration - no required stages
        coordinator2 = WorkflowCoordinator(mock_config)
        optional_stage = WorkflowStage("optional", lambda x: x, "Optional", False, True)
        coordinator2.add_stage(optional_stage)

        is_valid, error_msg = coordinator2.validate_workflow_configuration()
        assert is_valid is False
        assert "At least one stage must be marked as required" in error_msg

    def test_workflow_summary_generation(self, mock_config, sample_workflow_stages):
        """Test workflow summary generation."""
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # Get summary
        summary = coordinator.get_workflow_summary()

        assert summary['workflow_name'] == 'partnership_analysis'
        assert summary['total_stages'] == 4
        assert summary['required_stages'] == 3
        assert summary['optional_stages'] == 1
        assert summary['retryable_stages'] == 4
        assert summary['non_retryable_stages'] == 0
        assert len(summary['stage_names']) == 4

    def test_workflow_reset_and_reuse(self, mock_config, sample_workflow_stages):
        """Test workflow reset and reuse."""
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # First execution
        coordinator.initialize_execution({'first': 'execution'})
        success1, _, _ = coordinator.execute_workflow()

        # Reset
        coordinator.reset_workflow()

        # Second execution with different context
        coordinator.initialize_execution({'second': 'execution'})
        success2, _, _ = coordinator.execute_workflow()

        assert success1 is True
        assert success2 is True

        # Verify contexts are different
        assert coordinator.execution_context.get('first') is None
        assert coordinator.execution_context.get('second') == 'execution'

    @patch('src.python.orchestration.workflow_coordinator.datetime')
    def test_workflow_execution_timing(self, mock_datetime, mock_config, sample_workflow_stages):
        """Test workflow execution timing and metrics."""
        # Mock datetime to control timing
        mock_now = Mock()
        mock_now.isoformat.return_value = "2025-12-03T23:00:00"
        mock_datetime.utcnow.return_value = mock_now

        # Create coordinator
        coordinator = WorkflowCoordinator(mock_config)

        # Add stages
        for stage in sample_workflow_stages:
            coordinator.add_stage(stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Execute workflow
        success, error_msg, final_context = coordinator.execute_workflow()

        # Verify timing metrics
        assert 'start_time' in final_context
        assert 'end_time' in final_context
        assert 'duration_seconds' in final_context
        assert final_context['duration_seconds'] >= 0

        # Verify execution metrics
        assert final_context['stages_completed'] == 4
        assert final_context['stages_failed'] == 0
        assert final_context['stages_skipped'] == 0
        assert final_context['stages_total'] == 4