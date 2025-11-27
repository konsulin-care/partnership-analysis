"""
Unit tests for validators.py
"""

import json
import pytest
import math
from src.python.calculations.validators import (
    validate_calculations,
    validate_inputs,
)


@pytest.fixture
def sample_inputs():
    with open('tests/fixtures/sample_calculation_inputs.json', 'r') as f:
        return json.load(f)


def test_validate_calculations_valid(sample_inputs):
    results = {
        'profit': 15000000,
        'revenue': sample_inputs['revenue'],
        'total_costs': sample_inputs['revenue'] - 15000000,
        'breakeven_months': 34,  # 500M / 15M ≈ 33.33, ceil to 34
        'capex': sample_inputs['capex'],
        'monthly_profit': sample_inputs['monthly_profit'],
        'npv': -100000000,  # Example
        'cashflows': sample_inputs['cashflows'],
        'discount_rate': sample_inputs['discount_rate'],
        'revenue_share': sample_inputs['revenue'] * sample_inputs['share_pct'],
        'share_pct': sample_inputs['share_pct'],
        'profit_margin': 0.05,
        'roi': 0.2,
    }

    is_valid, errors = validate_calculations(results)
    assert is_valid
    assert len(errors) == 0


def test_validate_calculations_invalid_nan():
    results = {'profit': float('nan')}
    is_valid, errors = validate_calculations(results)
    assert not is_valid
    assert len(errors) > 0
    assert 'NaN' in errors[0]


def test_validate_calculations_invalid_profit_mismatch():
    results = {
        'profit': 1000000,
        'revenue': 2000000,
        'total_costs': 500000,  # Should be 2000000 - 500000 = 1500000 profit
    }
    is_valid, errors = validate_calculations(results)
    assert not is_valid
    assert any('Profit calculation mismatch' in error for error in errors)


def test_validate_calculations_invalid_breakeven():
    results = {
        'breakeven_months': 10,
        'capex': 1000000,
        'monthly_profit': 50000,  # Should be ceil(1000000/50000) = 20
    }
    is_valid, errors = validate_calculations(results)
    assert not is_valid
    assert any('Break-even calculation mismatch' in error for error in errors)


def test_validate_calculations_extreme_roi():
    results = {'roi': -3.0}  # Too negative
    is_valid, errors = validate_calculations(results)
    assert not is_valid
    assert any('ROI seems unreasonably negative' in error for error in errors)


def test_validate_inputs_valid(sample_inputs):
    is_valid, errors = validate_inputs(
        revenue=sample_inputs['revenue'],
        capex=sample_inputs['capex'],
        monthly_profit=sample_inputs['monthly_profit']
    )
    assert is_valid
    assert len(errors) == 0


def test_validate_inputs_invalid_negative():
    is_valid, errors = validate_inputs(revenue=-1000000)
    assert not is_valid
    assert len(errors) > 0
    assert 'Negative value not allowed' in errors[0]


def test_validate_inputs_invalid_nan():
    is_valid, errors = validate_inputs(revenue=float('nan'))
    assert not is_valid
    assert len(errors) > 0