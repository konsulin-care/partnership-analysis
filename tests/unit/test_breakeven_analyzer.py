"""
Unit tests for breakeven_analyzer.py
"""

import json
import pytest
from src.python.calculations.breakeven_analyzer import (
    calculate_breakeven,
    calculate_roi,
    calculate_payback_period,
)


@pytest.fixture
def sample_inputs():
    with open('tests/fixtures/sample_calculation_inputs.json', 'r') as f:
        return json.load(f)


def test_calculate_breakeven(sample_inputs):
    capex = sample_inputs['capex']
    monthly_profit = sample_inputs['monthly_profit']

    months = calculate_breakeven(capex, monthly_profit)
    expected = int((capex + monthly_profit - 1) // monthly_profit)  # Ceiling division
    assert months == expected
    assert months > 0


def test_calculate_breakeven_zero_profit():
    months = calculate_breakeven(1000000, 0)
    assert months == float('inf')


def test_calculate_breakeven_negative_profit():
    months = calculate_breakeven(1000000, -10000)
    assert months == float('inf')


def test_calculate_roi():
    roi = calculate_roi(1000000, 200000, 1)
    assert roi == 0.2  # 20%

    roi_multi_year = calculate_roi(1000000, 150000, 2)
    assert roi_multi_year == 0.3  # 30% over 2 years


def test_calculate_roi_zero_investment():
    roi = calculate_roi(0, 100000)
    assert roi == float('inf')


def test_calculate_payback_period(sample_inputs):
    cashflows = sample_inputs['cashflows'][1:]  # Skip initial investment
    initial_investment = abs(sample_inputs['cashflows'][0])

    payback = calculate_payback_period(initial_investment, cashflows)
    assert isinstance(payback, float)
    assert payback > 0


def test_calculate_payback_period_never():
    payback = calculate_payback_period(1000000, [100000, 100000, 100000])  # Total 300k < 1M
    assert payback == float('inf')