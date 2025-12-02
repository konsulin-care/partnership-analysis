"""
Integration tests for renderers module end-to-end workflow.

Tests complete rendering pipeline from Carbone JSON payload generation (using formatters)
through PDF rendering, including error scenarios, large payloads, and performance validation.
"""

import json
import os
import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import formatters for payload generation
from src.python.formatters import generate_carbone_json
from src.python.config import ConfigLoader

# Import renderers under test
from src.python.renderers import CarboneRenderer, PayloadValidator, ErrorHandler


@pytest.fixture
def sample_normalized_data():
    """Load and return comprehensive normalized data for testing."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_normalization_data.json"
    with open(fixture_path, 'r') as f:
        raw_data = json.load(f)

    # Transform raw data into normalized structure expected by formatters
    # This simulates the output of the schema normalization process
    normalized_data = {
        'metadata': {
            'document_id': raw_data['raw_metadata']['doc_id'],
            'generated_at': raw_data['raw_metadata']['timestamp'],
            'schema_version': '1.0'
        },
        'organizations': [
            {
                'name': 'Test Hub Operator',
                'role': 'hub_operator',
                'location': {
                    'city': raw_data['raw_organization']['city'],
                    'country': raw_data['raw_organization']['country']
                },
                'contact': {
                    'email': 'hub@test.com'
                }
            },
            {
                'name': raw_data['raw_organization']['clinic_name'],
                'role': 'tenant',
                'location': {
                    'city': raw_data['raw_organization']['city'],
                    'country': raw_data['raw_organization']['country']
                },
                'contact': {
                    'email': raw_data['raw_organization']['email']
                }
            }
        ],
        'partnership_terms': {
            'revenue_share_pct': float(raw_data['raw_partnership_terms']['share_percentage']),
            'capex_investment_idr': int(raw_data['raw_partnership_terms']['capex']),
            'capex_hub_contribution_idr': int(raw_data['raw_partnership_terms']['hub_capex'].replace('.', '')),
            'space_sqm': float(raw_data['raw_partnership_terms']['area']),
            'commitment_years': int(raw_data['raw_partnership_terms']['years']),
            'launch_timeline_days': int(raw_data['raw_partnership_terms']['timeline'])
        },
        'financial_data': {
            'scenarios': [
                {
                    'name': 'standalone',
                    'breakeven_months': int(raw_data['raw_financial_scenario']['breakeven']),
                    'monthly_costs': {
                        'rent_idr': int(raw_data['raw_financial_scenario']['costs']['monthly_rent']),
                        'staff_idr': int(str(raw_data['raw_financial_scenario']['costs']['staff_cost']).replace(',', '')),
                        'utilities_idr': int(raw_data['raw_financial_scenario']['costs']['utility_cost']),
                        'medical_supplies_idr': int(str(raw_data['raw_financial_scenario']['costs']['supplies']).replace(',', '')),
                        'capex_amortization_idr': int(str(raw_data['raw_financial_scenario']['costs']['amortization']).replace(' ', ''))
                    },
                    'annual_profit_idr': int(str(raw_data['raw_financial_scenario']['annual_profit']).replace(',', ''))
                },
                {
                    'name': 'hub',
                    'breakeven_months': 12,  # Example hub scenario
                    'monthly_costs': {
                        'rent_idr': 0,
                        'staff_idr': 25000000,
                        'utilities_idr': 5000000,
                        'medical_supplies_idr': 28500000,
                        'capex_amortization_idr': 4166667  # 50M / 12 months
                    },
                    'annual_profit_idr': 300000000
                }
            ],
            'year_1_revenue_idr': 3420000000,
            'year_3_cumulative_savings_idr': 500000000,
            'npv_discount_rate': 0.12
        },
        'research_data': {
            'market_benchmarks': [
                {
                    'category': 'hair_transplant_pricing',
                    'value': 30000000,
                    'unit': 'idr',
                    'source_citation': 'Medical Aesthetics Market Report 2025',
                    'research_date': '2025-01-15',
                    'confidence': 0.85
                },
                {
                    'category': 'market_growth_rate',
                    'value': 0.12,
                    'unit': 'pct',
                    'source_citation': 'Healthcare Industry Analysis',
                    'research_date': '2024-11-01',
                    'confidence': 0.92
                }
            ]
        },
        'quality_flags': {
            'missing_data_fields': [],
            'low_confidence_entities': [],
            'data_inconsistencies': []
        }
    }

    return normalized_data


@pytest.fixture
def config():
    """Create ConfigLoader instance for testing."""
    config_loader = ConfigLoader()
    return config_loader


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_carbone_sdk():
    """Mock CarboneSDK class."""
    mock_sdk = Mock()
    mock_sdk.return_value = mock_sdk  # Constructor returns instance
    mock_sdk.render.return_value = (b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nendobj\n%%EOF', 'unique_report_123')
    return mock_sdk


class TestRenderersEndToEnd:
    """End-to-end integration tests for all renderers."""

    def test_complete_rendering_pipeline(self, sample_normalized_data, config, temp_output_dir, mock_carbone_sdk):
        """Test complete rendering workflow from normalized data to PDF."""
        # Mock config to use temp directory
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en',
            'pdf_margin_top': 20,
            'pdf_margin_bottom': 20,
            'pdf_margin_left': 15,
            'pdf_margin_right': 15,
            'carbone_max_retries': 3,
            'carbone_retry_base_delay': 1.0,
            'carbone_retry_max_delay': 10.0
        }.get(key, default))

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            # Generate Carbone JSON payload using formatters
            carbone_payload = generate_carbone_json(sample_normalized_data, config)

            # Initialize renderer components
            renderer = CarboneRenderer(config)
            validator = PayloadValidator(config)
            error_handler = ErrorHandler(config)

            # Validate payload
            is_valid, errors = validator.validate_payload(carbone_payload)
            assert is_valid, f"Payload validation failed: {errors}"

            # Render PDF
            output_path = os.path.join(temp_output_dir, 'test_report.pdf')
            saved_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )[2]

            # Verify PDF was created
            assert saved_path is not None
            assert os.path.exists(saved_path)
            assert saved_path.endswith('test_report.pdf')

            # Verify PDF integrity
            is_valid_pdf, error_msg = renderer.validate_pdf_integrity(saved_path)
            assert is_valid_pdf, f"PDF validation failed: {error_msg}"

    def test_payload_validation_integration(self, sample_normalized_data, config, temp_output_dir):
        """Test payload validation works correctly in the pipeline."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en',
            'supported_languages': ['en', 'id']
        }.get(key, default))

        # Generate valid payload
        carbone_payload = generate_carbone_json(sample_normalized_data, config)
        validator = PayloadValidator(config)

        # Should validate successfully
        is_valid, errors = validator.validate_payload(carbone_payload)
        assert is_valid
        assert len(errors) == 0

        # Test invalid payload
        invalid_payload = carbone_payload.copy()
        del invalid_payload['data']['document']  # Remove required section

        is_valid, errors = validator.validate_payload(invalid_payload)
        assert not is_valid
        assert len(errors) > 0
        assert any('document' in error for error in errors)

        # Test validation with suggestions
        is_valid, errors, fixes, suggested = validator.validate_and_suggest_fixes(invalid_payload)
        assert not is_valid
        # The validator doesn't automatically add missing data sections, just top-level structure
        # Since data/template/options are present, no fixes are applied
        assert len(fixes) == 0
        assert suggested == invalid_payload  # No changes made

    def test_error_handling_integration(self, sample_normalized_data, config, temp_output_dir, mock_carbone_sdk):
        """Test error handling and recovery in the rendering pipeline."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1',
            'carbone_max_retries': 2,
            'carbone_retry_base_delay': 0.1,
            'carbone_retry_max_delay': 1.0
        }.get(key, default))

        # Generate payload
        carbone_payload = generate_carbone_json(sample_normalized_data, config)

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            renderer = CarboneRenderer(config)
            error_handler = ErrorHandler(config)

            # Test successful rendering
            output_path = os.path.join(temp_output_dir, 'success.pdf')
            success, error_msg, result_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )
            assert success
            assert result_path is not None
            assert os.path.exists(result_path)

    def test_error_scenarios(self, sample_normalized_data, config, temp_output_dir, mock_carbone_sdk):
        """Test various error scenarios in the rendering pipeline."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1'
        }.get(key, default))

        carbone_payload = generate_carbone_json(sample_normalized_data, config)

        # Test SDK initialization failure
        with patch('src.python.renderers.carbone_renderer.CarboneSDK', None):
            renderer = CarboneRenderer(config)
            with pytest.raises(RuntimeError, match="Carbone SDK is not installed"):
                renderer.initialize_carbone_client()

        # Test rendering failure with retry
        mock_sdk_instance = Mock()
        mock_sdk_instance.render.side_effect = ConnectionError("Network error")
        mock_carbone_sdk.return_value = mock_sdk_instance

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            renderer = CarboneRenderer(config)
            error_handler = ErrorHandler(config)

            output_path = os.path.join(temp_output_dir, 'error_test.pdf')
            success, error_msg, result_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )

            # Should eventually fail after retries
            assert not success
            assert "Network error" in error_msg  # Check for the actual error message
            assert result_path is None

    def test_file_output_paths_and_permissions(self, sample_normalized_data, config, temp_output_dir, mock_carbone_sdk):
        """Test that PDF files are created with correct paths and permissions."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1'
        }.get(key, default))

        carbone_payload = generate_carbone_json(sample_normalized_data, config)

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            renderer = CarboneRenderer(config)
            error_handler = ErrorHandler(config)

            # Test with subdirectory creation
            output_path = os.path.join(temp_output_dir, 'reports', 'analysis.pdf')
            success, _, result_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )

            assert success
            assert os.path.exists(result_path)
            assert os.path.dirname(result_path) == os.path.join(temp_output_dir, 'reports')

            # Check file permissions (should be readable)
            assert os.access(result_path, os.R_OK)

    @pytest.mark.extensive
    def test_performance_large_payload(self, config, temp_output_dir, mock_carbone_sdk):
        """Test performance with large payloads (marked as extensive)."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1',
            'carbone_max_retries': 1  # Reduce retries for performance test
        }.get(key, default))

        # Create large normalized data (multiple scenarios, many benchmarks)
        large_data = {
            'metadata': {'document_id': 'large_test', 'generated_at': '2025-01-01T00:00:00Z', 'schema_version': '1.0'},
            'organizations': [
                {'name': f'Organization {i}', 'role': 'tenant' if i % 2 else 'hub_operator'}
                for i in range(10)
            ],
            'partnership_terms': {
                'revenue_share_pct': 12.5,
                'capex_investment_idr': 100000000,
                'commitment_years': 3
            },
            'financial_data': {
                'scenarios': [
                    {
                        'name': f'scenario_{i}',
                        'breakeven_months': 12 + i,
                        'monthly_costs': {
                            'rent_idr': 20000000 + i * 1000000,
                            'staff_idr': 30000000 + i * 2000000
                        },
                        'annual_profit_idr': 200000000 + i * 50000000
                    }
                    for i in range(5)  # 5 scenarios
                ],
                'year_1_revenue_idr': 3000000000,
                'year_3_cumulative_savings_idr': 500000000,
                'npv_discount_rate': 0.12
            },
            'research_data': {
                'market_benchmarks': [
                    {
                        'category': f'benchmark_{i}',
                        'value': 1000000 + i * 10000,
                        'unit': 'idr',
                        'source_citation': f'Source {i}',
                        'research_date': '2025-01-01',
                        'confidence': 0.8
                    }
                    for i in range(50)  # 50 benchmarks
                ]
            }
        }

        # Mock slower rendering for performance test
        mock_client = Mock()
        mock_client.render.return_value = b'%PDF-1.4\n' + b'large content\n' * 1000 + b'%%EOF'
        mock_carbone_sdk.return_value = mock_client

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            carbone_payload = generate_carbone_json(large_data, config)
            renderer = CarboneRenderer(config)
            error_handler = ErrorHandler(config)

            # Measure execution time
            start_time = time.time()

            output_path = os.path.join(temp_output_dir, 'large_report.pdf')
            success, _, result_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # Verify success
            assert success
            assert os.path.exists(result_path)

            # Performance assertion (should complete within reasonable time)
            assert execution_time < 2.0  # Less than 2 seconds for large payload

            # Verify file size is reasonable
            file_size = os.path.getsize(result_path)
            assert file_size > 1000  # Should be substantial

    def test_component_integration(self, sample_normalized_data, config, temp_output_dir, mock_carbone_sdk):
        """Test that all renderer components work together correctly."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en',
            'supported_languages': ['en', 'id']
        }.get(key, default))

        carbone_payload = generate_carbone_json(sample_normalized_data, config)

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            # Initialize all components
            renderer = CarboneRenderer(config)
            validator = PayloadValidator(config)
            error_handler = ErrorHandler(config)

            # Test payload preparation
            prepared_payload = renderer.prepare_carbone_payload(carbone_payload['data'])
            assert 'data' in prepared_payload
            assert 'template' in prepared_payload
            assert 'options' in prepared_payload

            # Test validation
            is_valid, errors = validator.validate_payload(prepared_payload)
            assert is_valid, f"Validation failed: {errors}"

            # Test rendering with error handling
            output_path = os.path.join(temp_output_dir, 'integrated_test.pdf')
            success, error_msg, result_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )

            assert success, f"Rendering failed: {error_msg}"
            assert result_path is not None
            assert os.path.exists(result_path)

            # Test PDF validation
            is_valid_pdf, pdf_error = renderer.validate_pdf_integrity(result_path)
            assert is_valid_pdf, f"PDF validation failed: {pdf_error}"

    def test_graceful_degradation(self, sample_normalized_data, config, temp_output_dir, mock_carbone_sdk):
        """Test graceful degradation when rendering fails."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'carbone_secret_access_token': 'test_api_key_123',
            'carbone_template_id': 'test_template_v1'
        }.get(key, default))

        carbone_payload = generate_carbone_json(sample_normalized_data, config)

        # Mock SDK to fail on all attempts with retryable error, then succeed on fallback
        mock_client = Mock()
        call_count = 0

        def render_side_effect(file_or_template_id, json_data, options):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # Fail first 3 attempts (max retries)
                raise RuntimeError("Network timeout")  # Retryable error
            return (b'%PDF-1.4\nfallback content\n%%EOF', 'fallback_report_123')

        mock_client.render.side_effect = render_side_effect
        mock_carbone_sdk.return_value = mock_client

        with patch('src.python.renderers.carbone_renderer.CarboneSDK', mock_carbone_sdk):
            renderer = CarboneRenderer(config)
            error_handler = ErrorHandler(config)

            output_path = os.path.join(temp_output_dir, 'degradation_test.pdf')
            success, error_msg, result_path = error_handler.attempt_render_with_fallback(
                renderer.render_and_save,
                carbone_payload['data'],
                output_path
            )

            # Should succeed with fallback after exhausting retries
            assert success
            assert "Rendered with simplified payload" in error_msg
            assert result_path is not None
            assert os.path.exists(result_path)