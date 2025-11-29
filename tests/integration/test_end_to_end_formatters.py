"""
Integration tests for formatters module end-to-end workflow.

Tests complete formatting pipeline from normalized data to all output formats:
CSV tables, JSON serialization, BibTeX bibliography, Carbone JSON, and TXT intermediary.
"""

import json
import os
import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import Mock

# Import formatters under test
from src.python.formatters import (
    export_financial_tables_to_csv,
    serialize_to_json,
    generate_bibtex,
    generate_carbone_json,
    generate_intermediary_txt,
)
from src.python.config import ConfigLoader


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


class TestFormattersEndToEnd:
    """End-to-end integration tests for all formatters."""

    def test_complete_formatting_pipeline(self, sample_normalized_data, config, temp_output_dir):
        """Test complete formatting workflow from normalized data to all output formats."""
        # Mock config to use temp directory
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}',
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en',
            'pdf_margin_top': 20,
            'pdf_margin_bottom': 20,
            'pdf_margin_left': 15,
            'pdf_margin_right': 15
        }.get(key, default))

        # Execute all formatters
        csv_files = export_financial_tables_to_csv(sample_normalized_data, config)
        json_file = serialize_to_json(sample_normalized_data, config)
        bibtex_file = generate_bibtex(sample_normalized_data, config)
        carbone_payload = generate_carbone_json(sample_normalized_data, config)
        txt_file = generate_intermediary_txt(sample_normalized_data, config)

        # Verify CSV output
        assert len(csv_files) == 1
        assert os.path.exists(csv_files[0])
        assert csv_files[0].endswith('scenario_comparison.csv')

        # Verify JSON output
        assert os.path.exists(json_file)
        assert json_file.endswith('normalized_data.json')

        # Verify BibTeX output
        assert os.path.exists(bibtex_file)
        assert bibtex_file.endswith('references.bib')

        # Verify Carbone JSON payload
        assert isinstance(carbone_payload, dict)
        assert 'data' in carbone_payload
        assert 'template' in carbone_payload
        assert 'options' in carbone_payload

        # Verify TXT output
        assert os.path.exists(txt_file)
        assert txt_file.endswith('intermediary.txt')

    def test_output_content_validation(self, sample_normalized_data, config, temp_output_dir):
        """Test that generated files contain expected content."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}',
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en'
        }.get(key, default))

        # Generate outputs
        csv_files = export_financial_tables_to_csv(sample_normalized_data, config)
        json_file = serialize_to_json(sample_normalized_data, config)
        bibtex_file = generate_bibtex(sample_normalized_data, config)
        carbone_payload = generate_carbone_json(sample_normalized_data, config)
        txt_file = generate_intermediary_txt(sample_normalized_data, config)

        # Validate CSV content
        import pandas as pd
        df = pd.read_csv(csv_files[0])
        assert len(df) == 4  # 4 metrics
        assert 'Initial Investment' in df['Metric'].values
        assert 'Break-Even Timeline' in df['Metric'].values

        # Validate JSON content
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        assert json_data['metadata']['document_id'] == 'test_doc_123'
        assert len(json_data['organizations']) == 2
        assert json_data['partnership_terms']['revenue_share_pct'] == 12.5

        # Validate BibTeX content
        with open(bibtex_file, 'r', encoding='utf-8') as f:
            bibtex_content = f.read()
        assert '@misc{benchmark1_hairtransplantpricing,' in bibtex_content
        assert 'Medical Aesthetics Market Report 2025' in bibtex_content

        # Validate Carbone JSON structure
        assert carbone_payload['data']['document']['title'] == 'Partnership Analysis: Test Hub Operator x Test Clinic Ltd.'
        assert 'executive_summary' in carbone_payload['data']
        assert 'financial_analysis' in carbone_payload['data']

        # Validate TXT content
        with open(txt_file, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        assert 'PARTNERSHIP ANALYSIS INTERMEDIARY DOCUMENT' in txt_content
        assert 'EXECUTIVE SUMMARY' in txt_content
        assert 'MARKET RESEARCH FINDINGS' in txt_content

    def test_error_handling_partial_success(self, config, temp_output_dir):
        """Test error handling and partial success scenarios."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}'
        }.get(key, default))

        # Test with missing financial scenarios (should fail for CSV, succeed for others)
        incomplete_data = {
            'metadata': {'document_id': 'test', 'generated_at': '2025-01-01T00:00:00Z', 'schema_version': '1.0'},
            'organizations': [{'name': 'Test Clinic', 'role': 'tenant'}],
            'partnership_terms': {'revenue_share_pct': 10, 'capex_investment_idr': 100000000, 'commitment_years': 2},
            'financial_data': {'scenarios': []},  # Empty scenarios
            'research_data': {'market_benchmarks': []}
        }

        # CSV should fail
        with pytest.raises(ValueError, match="No financial scenarios found"):
            export_financial_tables_to_csv(incomplete_data, config)

        # JSON should succeed
        json_file = serialize_to_json(incomplete_data, config)
        assert os.path.exists(json_file)

        # BibTeX should succeed (with comment)
        bibtex_file = generate_bibtex(incomplete_data, config)
        assert os.path.exists(bibtex_file)

        # TXT should succeed
        txt_file = generate_intermediary_txt(incomplete_data, config)
        assert os.path.exists(txt_file)

    def test_file_output_paths_and_naming(self, sample_normalized_data, config, temp_output_dir):
        """Test that output files are created with correct paths and naming."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}'
        }.get(key, default))

        # Generate outputs
        csv_files = export_financial_tables_to_csv(sample_normalized_data, config)
        json_file = serialize_to_json(sample_normalized_data, config)
        bibtex_file = generate_bibtex(sample_normalized_data, config)
        txt_file = generate_intermediary_txt(sample_normalized_data, config)

        # Check file paths are in temp directory
        for file_path in [csv_files[0], json_file, bibtex_file, txt_file]:
            assert file_path.startswith(temp_output_dir)
            assert os.path.isabs(file_path)

        # Check specific filenames
        assert 'scenario_comparison.csv' in csv_files[0]
        assert 'normalized_data.json' in json_file
        assert 'references.bib' in bibtex_file
        assert 'intermediary.txt' in txt_file

    @pytest.mark.extensive
    def test_performance_large_dataset(self, config, temp_output_dir):
        """Test performance with large datasets (marked as extensive)."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}',
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en'
        }.get(key, default))

        # Create large normalized data (100 benchmarks, multiple scenarios)
        large_data = {
            'metadata': {'document_id': 'large_test', 'generated_at': '2025-01-01T00:00:00Z', 'schema_version': '1.0'},
            'organizations': [{'name': 'Large Clinic', 'role': 'tenant'}],
            'partnership_terms': {'revenue_share_pct': 10, 'capex_investment_idr': 100000000, 'commitment_years': 3},
            'financial_data': {
                'scenarios': [
                    {
                        'name': 'standalone',
                        'breakeven_months': 24,
                        'monthly_costs': {'rent_idr': 20000000, 'staff_idr': 30000000},
                        'annual_profit_idr': 200000000
                    },
                    {
                        'name': 'hub',
                        'breakeven_months': 12,
                        'monthly_costs': {'rent_idr': 0, 'staff_idr': 25000000},
                        'annual_profit_idr': 250000000
                    }
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
                    for i in range(100)  # 100 benchmarks
                ]
            }
        }

        # Measure execution time
        start_time = time.time()

        # Execute formatters
        csv_files = export_financial_tables_to_csv(large_data, config)
        json_file = serialize_to_json(large_data, config)
        bibtex_file = generate_bibtex(large_data, config)
        carbone_payload = generate_carbone_json(large_data, config)
        txt_file = generate_intermediary_txt(large_data, config)

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify outputs created
        assert len(csv_files) == 1
        assert os.path.exists(json_file)
        assert os.path.exists(bibtex_file)
        assert isinstance(carbone_payload, dict)
        assert os.path.exists(txt_file)

        # Performance assertion (should complete within reasonable time)
        assert execution_time < 5.0  # Less than 5 seconds for large dataset

        # Verify large BibTeX file has all entries
        with open(bibtex_file, 'r', encoding='utf-8') as f:
            bibtex_content = f.read()
        assert bibtex_content.count('@misc{') == 100  # 100 benchmark entries

    def test_formatter_independence(self, sample_normalized_data, config, temp_output_dir):
        """Test that formatters work independently and don't interfere with each other."""
        config.get = Mock(side_effect=lambda key, default=None: {
            'output_dir': temp_output_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}',
            'carbone_template_id': 'test_template_v1',
            'report_language': 'en'
        }.get(key, default))

        # Run formatters in different order
        txt_file = generate_intermediary_txt(sample_normalized_data, config)
        json_file = serialize_to_json(sample_normalized_data, config)
        bibtex_file = generate_bibtex(sample_normalized_data, config)
        csv_files = export_financial_tables_to_csv(sample_normalized_data, config)
        carbone_payload = generate_carbone_json(sample_normalized_data, config)

        # All should succeed regardless of order
        assert os.path.exists(txt_file)
        assert os.path.exists(json_file)
        assert os.path.exists(bibtex_file)
        assert len(csv_files) == 1
        assert isinstance(carbone_payload, dict)

        # Verify content integrity
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        assert json_data['metadata']['document_id'] == 'test_doc_123'