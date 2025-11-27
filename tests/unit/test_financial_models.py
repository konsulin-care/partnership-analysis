"""
Unit tests for financial_models.py
"""

import json
import pytest
from src.python.calculations.financial_models import (
    calculate_operational_costs,
    calculate_revenue_share,
    calculate_npv,
)


@pytest.fixture
def sample_config():
    with open('tests/fixtures/sample_config.json', 'r') as f:
        return json.load(f)


@pytest.fixture
def sample_inputs():
    with open('tests/fixtures/sample_calculation_inputs.json', 'r') as f:
        return json.load(f)


def test_calculate_operational_costs_standalone(sample_config, sample_inputs):
    revenue = sample_inputs['revenue']
    costs = calculate_operational_costs(revenue, 'standalone', sample_config)

    assert 'total_operational_costs' in costs
    assert costs['total_operational_costs'] > 0
    assert costs['rent'] == sample_config['standalone_rent_monthly']
    assert costs['staff'] == sample_config['standalone_staff_monthly']
    assert costs['revenue_share'] == 0


def test_calculate_operational_costs_hub(sample_config, sample_inputs):
    revenue = sample_inputs['revenue']
    costs = calculate_operational_costs(revenue, 'hub', sample_config)

    assert 'total_operational_costs' in costs
    assert costs['total_operational_costs'] > 0
    assert costs['rent'] == 0
    assert costs['revenue_share'] == revenue * sample_config['hub_revenue_share_pct']


def test_calculate_operational_costs_invalid_model(sample_config):
    with pytest.raises(ValueError):
        calculate_operational_costs(1000000, 'invalid', sample_config)


def test_calculate_revenue_share(sample_inputs):
    revenue = sample_inputs['revenue']
    share_pct = sample_inputs['share_pct']
    minimum = sample_inputs['minimum']

    share = calculate_revenue_share(revenue, share_pct, minimum)
    expected = revenue * share_pct
    assert share == expected  # Since expected > minimum


def test_calculate_revenue_share_with_minimum():
    revenue = 1000000
    share_pct = 0.05  # 50000
    minimum = 100000

    share = calculate_revenue_share(revenue, share_pct, minimum)
    assert share == minimum


def test_calculate_npv(sample_inputs):
    cashflows = sample_inputs['cashflows']
    discount_rate = sample_inputs['discount_rate']

    npv = calculate_npv(cashflows, discount_rate)
    assert isinstance(npv, float)
    # With the sample cashflows, NPV should be positive
    assert npv > 0


def test_calculate_npv_empty_cashflows():
    npv = calculate_npv([], 0.1)
    assert npv == 0.0