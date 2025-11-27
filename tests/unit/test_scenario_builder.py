"""
Unit tests for scenario_builder.py
"""

import json
import pytest
from src.python.calculations.scenario_builder import (
    generate_sensitivity_table,
    generate_scenario_comparison,
)


@pytest.fixture
def sample_config():
    with open('tests/fixtures/sample_config.json', 'r') as f:
        return json.load(f)


@pytest.fixture
def sample_inputs():
    with open('tests/fixtures/sample_calculation_inputs.json', 'r') as f:
        return json.load(f)


def test_generate_sensitivity_table(sample_config, sample_inputs):
    pd = pytest.importorskip("pandas")

    base_revenue = sample_inputs['revenue']
    variance_range = sample_inputs['variance_range']
    model_type = sample_inputs['model_type']

    df = generate_sensitivity_table(base_revenue, variance_range, model_type, sample_config)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(variance_range)
    assert 'variance_pct' in df.columns
    assert 'revenue' in df.columns
    assert 'total_costs' in df.columns
    assert 'profit' in df.columns
    assert 'profit_margin' in df.columns

    # Check that revenues vary as expected
    for i, variance in enumerate(variance_range):
        expected_revenue = base_revenue * (1 + variance)
        assert abs(df.iloc[i]['revenue'] - expected_revenue) < 1e-6


def test_generate_scenario_comparison(sample_config):
    pd = pytest.importorskip("pandas")

    scenarios = {
        'standalone_high': {
            'revenue': 300000000,
            'model_type': 'standalone',
            'capex': 600000000,
        },
        'hub_low': {
            'revenue': 250000000,
            'model_type': 'hub',
            'capex': 400000000,
        },
    }

    df = generate_scenario_comparison(scenarios, sample_config)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'scenario' in df.columns
    assert 'model_type' in df.columns
    assert 'revenue' in df.columns
    assert 'profit' in df.columns

    # Check scenario names
    assert set(df['scenario']) == {'standalone_high', 'hub_low'}