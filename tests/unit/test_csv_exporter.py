"""
Unit tests for csv_exporter.py
"""

import json
import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import Mock
from src.python.formatters.csv_exporter import (
    export_financial_tables_to_csv,
    _calculate_scenario_metrics,
    _calculate_advantage,
    _format_dataframe_values,
)


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'output_dir': 'outputs',
        'currency_format': 'IDR {:,.0f}',
        'unit_format': '{:.1f}'
    }.get(key, default)
    return config


@pytest.fixture
def mock_normalized_data():
    """Mock normalized data with financial scenarios."""
    return {
        'financial_data': {
            'scenarios': [
                {
                    'name': 'standalone',
                    'breakeven_months': 24.0,
                    'monthly_costs': {'rent': 20000000, 'staff': 30000000},
                    'annual_profit_idr': 200000000
                },
                {
                    'name': 'hub',
                    'breakeven_months': 12.0,
                    'monthly_costs': {'rent': 0, 'staff': 25000000},
                    'annual_profit_idr': 250000000
                }
            ]
        },
        'partnership_terms': {
            'capex_investment_idr': 200000000,
            'capex_hub_contribution_idr': 50000000
        }
    }


@pytest.fixture
def mock_normalized_data_missing_scenarios():
    """Mock normalized data without scenarios."""
    return {
        'financial_data': {
            'scenarios': []
        },
        'partnership_terms': {}
    }


@pytest.fixture
def mock_normalized_data_missing_financial():
    """Mock normalized data without financial_data."""
    return {
        'partnership_terms': {}
    }


def test_export_financial_tables_to_csv_success(mock_normalized_data, mock_config):
    """Test successful CSV export with valid data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir,
            'currency_format': 'IDR {:,.0f}',
            'unit_format': '{:.1f}'
        }.get(key, default)

        file_paths = export_financial_tables_to_csv(mock_normalized_data, mock_config)

        assert len(file_paths) == 1
        assert os.path.exists(file_paths[0])
        assert file_paths[0].endswith('scenario_comparison.csv')

        # Verify CSV content
        df = pd.read_csv(file_paths[0])
        assert len(df) == 4  # 4 metrics
        assert list(df.columns) == ['Metric', 'Standalone', 'Hub', 'Advantage']

        # Check specific values
        capex_row = df[df['Metric'] == 'Initial Investment']
        assert 'IDR 200,000,000' in capex_row['Standalone'].values[0]
        assert 'IDR 150,000,000' in capex_row['Hub'].values[0]
        assert '25.0%' in capex_row['Advantage'].values[0]


def test_export_financial_tables_to_csv_missing_scenarios(mock_normalized_data_missing_scenarios, mock_config):
    """Test CSV export fails with missing scenarios."""
    with pytest.raises(ValueError, match="No financial scenarios found"):
        export_financial_tables_to_csv(mock_normalized_data_missing_scenarios, mock_config)


def test_export_financial_tables_to_csv_missing_financial(mock_normalized_data_missing_financial, mock_config):
    """Test CSV export fails with missing financial data."""
    with pytest.raises(ValueError, match="No financial scenarios found"):
        export_financial_tables_to_csv(mock_normalized_data_missing_financial, mock_config)


def test_export_financial_tables_to_csv_file_error(mock_normalized_data, mock_config):
    """Test CSV export handles file write errors."""
    mock_config.get.side_effect = lambda key, default=None: {
        'output_dir': '/invalid/path',
        'currency_format': 'IDR {:,.0f}',
        'unit_format': '{:.1f}'
    }.get(key, default)

    with pytest.raises(OSError, match="Failed to export CSV"):
        export_financial_tables_to_csv(mock_normalized_data, mock_config)


def test_calculate_scenario_metrics(mock_normalized_data):
    """Test scenario metrics calculation."""
    standalone = mock_normalized_data['financial_data']['scenarios'][0]
    hub = mock_normalized_data['financial_data']['scenarios'][1]
    partnership_terms = mock_normalized_data['partnership_terms']
    mock_config = Mock()
    mock_config.get.return_value = 'IDR {:,.0f}'

    metrics = _calculate_scenario_metrics(standalone, hub, partnership_terms, mock_config)

    assert len(metrics) == 4
    assert metrics[0]['Metric'] == 'Initial Investment'
    assert metrics[0]['Standalone'] == 200000000
    assert metrics[0]['Hub'] == 150000000
    assert metrics[0]['Advantage'] == '25.0%'

    assert metrics[1]['Metric'] == 'Break-Even Timeline'
    assert metrics[1]['Standalone'] == 24.0
    assert metrics[1]['Hub'] == 12.0
    assert metrics[1]['Advantage'] == '50.0%'

    assert metrics[2]['Metric'] == 'Monthly Operating Cost'
    assert metrics[2]['Standalone'] == 50000000
    assert metrics[2]['Hub'] == 25000000
    assert metrics[2]['Advantage'] == '50.0%'

    assert metrics[3]['Metric'] == 'Year 1 Profit'
    assert metrics[3]['Standalone'] == 200000000
    assert metrics[3]['Hub'] == 250000000
    assert metrics[3]['Advantage'] == '25.0%'


def test_calculate_advantage():
    """Test advantage percentage calculation."""
    # Lower better (costs)
    advantage = _calculate_advantage(100, 80, lower_better=True)
    assert advantage == '20.0%'

    # Higher better (profits)
    advantage = _calculate_advantage(100, 120, lower_better=False)
    assert advantage == '20.0%'

    # Zero standalone value
    advantage = _calculate_advantage(0, 100, lower_better=True)
    assert advantage == 'N/A'


def test_format_dataframe_values():
    """Test DataFrame value formatting."""
    mock_config = Mock()
    mock_config.get.side_effect = lambda key, default=None: {
        'currency_format': 'IDR {:,.0f}',
        'unit_format': '{:.1f}'
    }.get(key, default)

    data = {
        'Metric': ['Test Metric'],
        'Standalone': [1000000],
        'Hub': [800000],
        'Advantage': ['20.0%']
    }
    df = pd.DataFrame(data)

    formatted_df = _format_dataframe_values(df, mock_config)

    assert formatted_df.loc[0, 'Standalone'] == 'IDR 1,000,000'
    assert formatted_df.loc[0, 'Hub'] == 'IDR 800,000'
    assert formatted_df.loc[0, 'Advantage'] == '20.0%'  # Already formatted


def test_format_dataframe_values_with_none():
    """Test DataFrame formatting with None values."""
    mock_config = Mock()
    mock_config.get.return_value = 'IDR {:,.0f}'

    data = {
        'Metric': ['Test Metric'],
        'Standalone': [None],
        'Hub': [1000000],
        'Advantage': ['N/A']
    }
    df = pd.DataFrame(data)

    formatted_df = _format_dataframe_values(df, mock_config)

    assert formatted_df.loc[0, 'Standalone'] == 'None'
    assert formatted_df.loc[0, 'Hub'] == 'IDR 1,000,000'