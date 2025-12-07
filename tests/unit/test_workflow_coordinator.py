"""
Unit tests for workflow_coordinator.py
"""

from unittest.mock import Mock, patch, call
import pytest
from src.python.orchestration.workflow_coordinator import WorkflowCoordinator, WorkflowStage
from src.python.config.config_loader import ConfigLoader
from src.python.orchestration.logger import Logger
from src.python.orchestration.state_manager import StateManager
from src.python.orchestration.error_handler import OrchestrationErrorHandler

@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock(spec=ConfigLoader)
    config.get.side_effect = lambda key, default=None: {
        'workflow_name': 'test_workflow',
        'max_concurrent_stages': 1,
        'enable_parallel_execution': 'false',
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
def mock_error_handler():
    """Mock OrchestrationErrorHandler instance."""
    return Mock(spec=OrchestrationErrorHandler)

@pytest.fixture
def sample_stage():
    """Sample workflow stage for testing."""
    def sample_func(context):
        return f"result_{context.get('stage_name', 'default')}"

    return WorkflowStage(
        name="test_stage",
        func=sample_func,
        description="Test stage for unit testing",
        required=True,
        retryable=True
    )

@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        'execution_id': 'test_execution_123',
        'workflow_name': 'test_workflow',
        'data': {'key': 'value'}
    }

class TestWorkflowStage:
    """Test cases for WorkflowStage class."""

    def test_workflow_stage_init(self, sample_stage):
        """Test WorkflowStage initialization."""
        assert sample_stage.name == "test_stage"
        assert sample_stage.description == "Test stage for unit testing"
        assert sample_stage.required is True
        assert sample_stage.retryable is True
        assert callable(sample_stage.func)

    def test_workflow_stage_execute(self, sample_stage):
        """Test WorkflowStage execution."""
        context = {'stage_name': 'test_execution'}
        result = sample_stage.execute(context)
        assert result == "result_test_execution"

class TestWorkflowCoordinator:
    """Test cases for WorkflowCoordinator class."""

    def test_init_with_defaults(self, mock_config):
        """Test initialization with default parameters."""
        coordinator = WorkflowCoordinator(mock_config)

        assert coordinator.config == mock_config
        assert coordinator.workflow_name == 'test_workflow'
        assert coordinator.max_concurrent_stages == 1
        assert coordinator.enable_parallel_execution is False
        assert isinstance(coordinator.logger, Logger)
        assert isinstance(coordinator.state_manager, StateManager)
        assert isinstance(coordinator.error_handler, OrchestrationErrorHandler)
        assert coordinator.stages == []

    def test_init_with_custom_components(self, mock_config, mock_logger, mock_state_manager, mock_error_handler):
        """Test initialization with custom components."""
        coordinator = WorkflowCoordinator(
            mock_config, mock_logger, mock_state_manager, mock_error_handler
        )

        assert coordinator.logger == mock_logger
        assert coordinator.state_manager == mock_state_manager
        assert coordinator.error_handler == mock_error_handler

    def test_add_stage(self, mock_config, sample_stage):
        """Test adding a single stage."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        assert len(coordinator.stages) == 1
        assert coordinator.stages[0] == sample_stage

    def test_add_stages(self, mock_config, sample_stage):
        """Test adding multiple stages."""
        coordinator = WorkflowCoordinator(mock_config)
        stages = [sample_stage, sample_stage]  # Using same stage for simplicity
        coordinator.add_stages(stages)

        assert len(coordinator.stages) == 2

    def test_initialize_execution(self, mock_config, sample_stage):
        """Test execution initialization."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        execution_id = coordinator.initialize_execution({'test': 'data'})

        assert execution_id is not None
        assert coordinator.execution_id == execution_id
        assert coordinator.execution_context['test'] == 'data'
        assert coordinator.execution_context['execution_id'] == execution_id
        assert coordinator.execution_context['stages_completed'] == 0

    def test_initialize_execution_calls_state_manager(self, mock_config, mock_state_manager, sample_stage):
        """Test that initialize_execution calls state manager correctly."""
        coordinator = WorkflowCoordinator(mock_config, state_manager=mock_state_manager)
        coordinator.add_stage(sample_stage)

        initial_context = {'test': 'data'}
        execution_id = coordinator.initialize_execution(initial_context)

        mock_state_manager.start_execution.assert_called_once()
        call_args = mock_state_manager.start_execution.call_args
        assert call_args[0][0] == 'test_workflow'
        assert call_args[0][1] == initial_context

    def test_execute_workflow_no_stages(self, mock_config):
        """Test workflow execution with no stages."""
        coordinator = WorkflowCoordinator(mock_config)

        with pytest.raises(RuntimeError, match="Workflow execution not initialized"):
            coordinator.execute_workflow()

    def test_execute_workflow_no_initialization(self, mock_config, sample_stage):
        """Test workflow execution without initialization."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        with pytest.raises(RuntimeError, match="Workflow execution not initialized"):
            coordinator.execute_workflow()

    @patch('src.python.orchestration.workflow_coordinator.WorkflowCoordinator._execute_stage_with_error_handling')
    def test_execute_workflow_success(self, mock_execute_stage, mock_config, sample_stage):
        """Test successful workflow execution."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Mock successful stage execution
        mock_execute_stage.return_value = (True, "", "stage_result")

        success, error_msg, context = coordinator.execute_workflow()

        assert success is True
        assert error_msg == ""
        assert context['stages_completed'] == 1
        assert context['stages_failed'] == 0

    @patch('src.python.orchestration.workflow_coordinator.WorkflowCoordinator._execute_stage_with_error_handling')
    def test_execute_workflow_stage_failure_required(self, mock_execute_stage, mock_config, sample_stage):
        """Test workflow execution with required stage failure."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Mock failed stage execution
        mock_execute_stage.return_value = (False, "Stage failed", None)

        success, error_msg, context = coordinator.execute_workflow()

        assert success is False
        assert "Required stages failed" in error_msg
        assert context['stages_failed'] == 1

    @patch('src.python.orchestration.workflow_coordinator.WorkflowCoordinator._execute_stage_with_error_handling')
    def test_execute_workflow_stage_failure_optional(self, mock_execute_stage, mock_config):
        """Test workflow execution with optional stage failure."""
        coordinator = WorkflowCoordinator(mock_config)

        # Add an optional stage
        def optional_func(context):
            return "optional_result"

        optional_stage = WorkflowStage(
            name="optional_stage",
            func=optional_func,
            description="Optional test stage",
            required=False,
            retryable=True
        )

        coordinator.add_stage(optional_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Mock failed stage execution
        mock_execute_stage.return_value = (False, "Optional stage failed", None)

        success, error_msg, context = coordinator.execute_workflow()

        assert success is True  # Should continue with optional stage failure
        assert context['stages_failed'] == 1
        assert context['stages_completed'] == 0

    def test_execute_workflow_exception_handling(self, mock_config, sample_stage):
        """Test workflow execution with exception handling."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Mock the stage execution to raise an exception
        with patch.object(coordinator, '_execute_stage_with_error_handling') as mock_execute:
            mock_execute.side_effect = Exception("Unexpected error")

            success, error_msg, context = coordinator.execute_workflow()

            assert success is False
            assert "Required stages failed" in error_msg
            assert context['stages_failed'] == 1

    def test_execute_stage_with_error_handling_success(self, mock_config, sample_stage, sample_context):
        """Test successful stage execution with error handling."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution(sample_context)

        # Mock the error handler
        with patch.object(coordinator.error_handler, 'attempt_stage_execution') as mock_error_handler:
            mock_error_handler.return_value = (True, "", "stage_result")

            success, error_msg, result = coordinator._execute_stage_with_error_handling(sample_stage)

            assert success is True
            assert error_msg == ""
            assert result == "stage_result"

    def test_execute_stage_with_error_handling_failure(self, mock_config, sample_stage, sample_context):
        """Test failed stage execution with error handling."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution(sample_context)

        # Mock the error handler
        with patch.object(coordinator.error_handler, 'attempt_stage_execution') as mock_error_handler:
            mock_error_handler.return_value = (False, "Stage failed", None)

            success, error_msg, result = coordinator._execute_stage_with_error_handling(sample_stage)

            assert success is False
            assert error_msg == "Stage failed"
            assert result is None

    def test_prepare_stage_context(self, mock_config, sample_stage, sample_context):
        """Test stage context preparation."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution(sample_context)

        stage_context = coordinator._prepare_stage_context(sample_stage)

        assert stage_context['current_stage'] == "test_stage"
        assert stage_context['stage_index'] == 0
        assert stage_context['total_stages'] == 1
        assert 'stage_start_time' in stage_context
        assert stage_context['stage_required'] is True

    def test_update_context_from_stage(self, mock_config, sample_stage):
        """Test context update from stage results."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        stage_result = "test_result"
        coordinator._update_context_from_stage(sample_stage, stage_result)

        assert coordinator.execution_context['stage_test_stage_result'] == "test_result"
        assert 'stage_test_stage_metadata' in coordinator.execution_context

    def test_finalize_execution_success(self, mock_config, mock_state_manager, sample_stage):
        """Test successful execution finalization."""
        coordinator = WorkflowCoordinator(mock_config, state_manager=mock_state_manager)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Mock time for testing
        with patch('src.python.orchestration.workflow_coordinator.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.isoformat.return_value = "2025-12-03T23:00:00"
            mock_datetime.utcnow.return_value = mock_now

            coordinator._finalize_execution(True, "Success")

            assert coordinator.execution_end_time == mock_now
            assert coordinator.execution_context['final_status'] == 'success'
            assert coordinator.execution_context['final_message'] == 'Success'

            # Verify state manager was called
            mock_state_manager.end_execution.assert_called_once()

    def test_finalize_execution_failure(self, mock_config, mock_state_manager, sample_stage):
        """Test failed execution finalization."""
        coordinator = WorkflowCoordinator(mock_config, state_manager=mock_state_manager)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        coordinator._finalize_execution(False, "Failed")

        assert coordinator.execution_context['final_status'] == 'failed'
        assert coordinator.execution_context['final_message'] == 'Failed'

    def test_get_current_state(self, mock_config, sample_stage):
        """Test getting current execution state."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        state = coordinator.get_current_state()

        assert state['execution_id'] == coordinator.execution_id
        assert state['workflow_name'] == 'test_workflow'
        assert state['total_stages'] == 1
        assert 'context' in state

    def test_get_stage_status(self, mock_config, sample_stage):
        """Test getting stage status information."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        stage_status = coordinator.get_stage_status()

        assert len(stage_status) == 1
        assert stage_status[0]['name'] == "test_stage"
        assert stage_status[0]['required'] is True
        assert stage_status[0]['executed'] is False

    def test_reset_workflow(self, mock_config, sample_stage):
        """Test workflow reset."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Reset
        coordinator.reset_workflow()

        assert coordinator.execution_id is None
        assert coordinator.execution_context == {}
        assert coordinator.execution_start_time is None
        assert coordinator.execution_end_time is None
        assert coordinator.current_stage_index == 0

    def test_validate_workflow_configuration_valid(self, mock_config, sample_stage):
        """Test valid workflow configuration."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        is_valid, error_msg = coordinator.validate_workflow_configuration()

        assert is_valid is True
        assert error_msg == "Workflow configuration is valid"

    def test_validate_workflow_configuration_no_stages(self, mock_config):
        """Test workflow configuration with no stages."""
        coordinator = WorkflowCoordinator(mock_config)

        is_valid, error_msg = coordinator.validate_workflow_configuration()

        assert is_valid is False
        assert "No stages defined" in error_msg

    def test_validate_workflow_configuration_duplicate_names(self, mock_config):
        """Test workflow configuration with duplicate stage names."""
        coordinator = WorkflowCoordinator(mock_config)

        def dummy_func(context):
            return "result"

        stage1 = WorkflowStage("duplicate_name", dummy_func)
        stage2 = WorkflowStage("duplicate_name", dummy_func)

        coordinator.add_stages([stage1, stage2])

        is_valid, error_msg = coordinator.validate_workflow_configuration()

        assert is_valid is False
        assert "Duplicate stage names" in error_msg

    def test_validate_workflow_configuration_no_required_stages(self, mock_config):
        """Test workflow configuration with no required stages."""
        coordinator = WorkflowCoordinator(mock_config)

        def dummy_func(context):
            return "result"

        stage = WorkflowStage("optional_stage", dummy_func, required=False)
        coordinator.add_stage(stage)

        is_valid, error_msg = coordinator.validate_workflow_configuration()

        assert is_valid is False
        assert "At least one stage must be marked as required" in error_msg

    def test_get_workflow_summary(self, mock_config, sample_stage):
        """Test getting workflow summary."""
        coordinator = WorkflowCoordinator(mock_config)
        coordinator.add_stage(sample_stage)

        summary = coordinator.get_workflow_summary()

        assert summary['workflow_name'] == 'test_workflow'
        assert summary['total_stages'] == 1
        assert summary['required_stages'] == 1
        assert summary['optional_stages'] == 0
        assert summary['retryable_stages'] == 1
        assert summary['stage_names'] == ["test_stage"]

    def test_workflow_with_multiple_stages(self, mock_config):
        """Test workflow with multiple stages of different types."""
        coordinator = WorkflowCoordinator(mock_config)

        def stage1_func(context):
            return "stage1_result"

        def stage2_func(context):
            return "stage2_result"

        def stage3_func(context):
            return "stage3_result"

        stage1 = WorkflowStage("required_retryable", stage1_func, required=True, retryable=True)
        stage2 = WorkflowStage("required_non_retryable", stage2_func, required=True, retryable=False)
        stage3 = WorkflowStage("optional_stage", stage3_func, required=False, retryable=True)

        coordinator.add_stages([stage1, stage2, stage3])

        # Test validation
        is_valid, error_msg = coordinator.validate_workflow_configuration()
        assert is_valid is True

        # Test summary
        summary = coordinator.get_workflow_summary()
        assert summary['total_stages'] == 3
        assert summary['required_stages'] == 2
        assert summary['optional_stages'] == 1
        assert summary['retryable_stages'] == 2
        assert summary['non_retryable_stages'] == 1

    @patch('src.python.orchestration.workflow_coordinator.WorkflowCoordinator._execute_stage_with_error_handling')
    def test_workflow_execution_with_mixed_stages(self, mock_execute_stage, mock_config):
        """Test workflow execution with mixed stage types."""
        coordinator = WorkflowCoordinator(mock_config)

        def stage1_func(context):
            return "stage1_result"

        def stage2_func(context):
            return "stage2_result"

        stage1 = WorkflowStage("required_stage", stage1_func, required=True, retryable=True)
        stage2 = WorkflowStage("optional_stage", stage2_func, required=False, retryable=True)

        coordinator.add_stages([stage1, stage2])

        # Initialize execution
        coordinator.initialize_execution({'test': 'data'})

        # Mock stage executions
        mock_execute_stage.side_effect = [
            (True, "", "stage1_result"),  # Stage 1 succeeds
            (False, "Optional failed", None)  # Stage 2 fails but is optional
        ]

        success, error_msg, context = coordinator.execute_workflow()

        assert success is True  # Should succeed because optional stage failure is allowed
        assert context['stages_completed'] == 1
        assert context['stages_failed'] == 1