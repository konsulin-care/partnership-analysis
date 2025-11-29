"""
Unit tests for txt_intermediary.py
"""

import os
import tempfile
import pytest
from unittest.mock import Mock
from src.python.formatters.txt_intermediary import (
    generate_intermediary_txt,
    _generate_header,
    _generate_executive_summary,
    _generate_market_research,
    _generate_partnership_terms,
    _generate_financial_analysis,
    _generate_quality_notes,
)


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'output_dir': 'outputs'
    }.get(key, default)
    return config


@pytest.fixture
def mock_normalized_data():
    """Mock normalized data with all required sections."""
    return {
        'metadata': {
            'document_id': 'test_doc_123',
            'generated_at': '2025-11-28T10:00:00Z',
            'schema_version': '1.0'
        },
        'organizations': [
            {
                'name': 'Test Partner Clinic',
                'role': 'partner'
            }
        ],
        'partnership_terms': {
            'revenue_share_pct': 12.5,
            'minimum_monthly_fee_idr': 50000000,
            'capex_investment_idr': 200000000,
            'capex_hub_contribution_idr': 50000000,
            'commitment_years': 3,
            'space_sqm': 150,
            'launch_timeline_days': 90
        },
        'financial_data': {
            'scenarios': [
                {
                    'name': 'standalone',
                    'monthly_revenue_idr': 285000000,
                    'monthly_costs': {'rent_idr': 20000000, 'staff_idr': 30000000},
                    'monthly_profit_idr': 175000000,
                    'breakeven_months': 24
                },
                {
                    'name': 'hub',
                    'monthly_revenue_idr': 285000000,
                    'monthly_costs': {'rent_idr': 0, 'staff_idr': 25000000},
                    'monthly_profit_idr': 200000000,
                    'breakeven_months': 12
                }
            ],
            'year_1_revenue_idr': 3420000000,
            'year_3_cumulative_savings_idr': 500000000,
            'npv_discount_rate': 0.1
        },
        'research_data': {
            'market_benchmarks': [
                {
                    'category': 'hair_transplant_pricing',
                    'value': 30000000,
                    'unit': 'idr',
                    'source_citation': 'Market Report 2025',
                    'confidence': 0.85
                }
            ]
        },
        'quality_flags': {
            'missing_data_fields': ['optional_field'],
            'low_confidence_entities': ['benchmark_1'],
            'data_inconsistencies': ['minor_issue']
        }
    }


@pytest.fixture
def mock_normalized_data_missing_keys():
    """Mock normalized data missing required keys."""
    return {
        'metadata': {},
        # Missing organizations, partnership_terms, financial_data
    }


def test_generate_intermediary_txt_success(mock_normalized_data, mock_config):
    """Test successful TXT generation with valid data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        file_path = generate_intermediary_txt(mock_normalized_data, mock_config)

        assert os.path.exists(file_path)
        assert file_path.endswith('intermediary.txt')

        # Verify content structure
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'PARTNERSHIP ANALYSIS INTERMEDIARY DOCUMENT' in content
        assert 'EXECUTIVE SUMMARY' in content
        assert 'MARKET RESEARCH FINDINGS' in content
        assert 'PARTNERSHIP TERMS' in content
        assert 'FINANCIAL ANALYSIS' in content
        assert 'QUALITY FLAGS AND NOTES' in content


def test_generate_intermediary_txt_empty_data(mock_config):
    """Test TXT generation fails with empty data."""
    with pytest.raises(ValueError, match="Normalized data cannot be empty"):
        generate_intermediary_txt({}, mock_config)


def test_generate_intermediary_txt_missing_keys(mock_normalized_data_missing_keys, mock_config):
    """Test TXT generation fails with missing required keys."""
    with pytest.raises(ValueError, match="Missing required keys in normalized data"):
        generate_intermediary_txt(mock_normalized_data_missing_keys, mock_config)


def test_generate_intermediary_txt_file_error(mock_normalized_data, mock_config):
    """Test TXT generation handles file write errors."""
    mock_config.get.side_effect = lambda key, default=None: {
        'output_dir': '/invalid/path'
    }.get(key, default)

    with pytest.raises(OSError, match="Failed to write intermediary TXT file"):
        generate_intermediary_txt(mock_normalized_data, mock_config)


def test_generate_header(mock_normalized_data):
    """Test header generation."""
    result = _generate_header(mock_normalized_data)

    assert 'PARTNERSHIP ANALYSIS INTERMEDIARY DOCUMENT' in result
    assert 'Document ID: test_doc_123' in result
    assert 'Generated At: 2025-11-28T10:00:00Z' in result
    assert 'Schema Version: 1.0' in result


def test_generate_executive_summary(mock_normalized_data):
    """Test executive summary generation."""
    result = _generate_executive_summary(mock_normalized_data)

    assert 'EXECUTIVE SUMMARY' in result
    assert 'Test Partner Clinic' in result
    assert 'Hub Model Breakeven: 12 months' in result
    assert 'Standalone Model Breakeven: 24 months' in result


def test_generate_market_research(mock_normalized_data):
    """Test market research generation with data."""
    result = _generate_market_research(mock_normalized_data)

    assert 'MARKET RESEARCH FINDINGS' in result
    assert 'hair_transplant_pricing: 30000000 idr' in result
    assert 'Source: Market Report 2025' in result
    assert 'Confidence: 0.85' in result


def test_generate_market_research_no_data():
    """Test market research generation with no data."""
    data = {'research_data': {'market_benchmarks': []}}
    result = _generate_market_research(data)

    assert 'MARKET RESEARCH FINDINGS' in result
    assert 'No market research data available' in result


def test_generate_partnership_terms(mock_normalized_data):
    """Test partnership terms generation."""
    result = _generate_partnership_terms(mock_normalized_data)

    assert 'PARTNERSHIP TERMS' in result
    assert 'Revenue Sharing: 12.5% of monthly revenue' in result
    assert 'Minimum Monthly Fee: IDR 50,000,000' in result
    assert 'CAPEX Investment (Tenant): IDR 200,000,000' in result
    assert 'Commitment Period: 3 years' in result


def test_generate_financial_analysis(mock_normalized_data):
    """Test financial analysis generation."""
    result = _generate_financial_analysis(mock_normalized_data)

    assert 'FINANCIAL ANALYSIS' in result
    assert 'Standalone Scenario:' in result
    assert 'Hub Scenario:' in result
    assert 'Year 1 Revenue Projection: IDR 3,420,000,000' in result
    assert 'Year 3 Cumulative Savings: IDR 500,000,000' in result


def test_generate_financial_analysis_no_scenarios():
    """Test financial analysis generation with no scenarios."""
    data = {'financial_data': {'scenarios': []}}
    result = _generate_financial_analysis(data)

    assert 'FINANCIAL ANALYSIS' in result
    assert 'No financial scenarios available' in result


def test_generate_quality_notes(mock_normalized_data):
    """Test quality notes generation with flags."""
    result = _generate_quality_notes(mock_normalized_data)

    assert 'QUALITY FLAGS AND NOTES' in result
    assert 'Missing Data Fields: optional_field' in result
    assert 'Low Confidence Entities: benchmark_1' in result
    assert 'Data Inconsistencies: minor_issue' in result


def test_generate_quality_notes_no_flags():
    """Test quality notes generation with no flags."""
    data = {'quality_flags': {}}
    result = _generate_quality_notes(data)

    assert 'QUALITY FLAGS AND NOTES' in result
    assert 'No quality issues identified' in result