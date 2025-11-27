"""
Breakeven Analyzer Module

Provides break-even analysis and ROI calculations for partnership scenarios.
"""

from typing import Dict, Any, Tuple
import numpy as np


def calculate_breakeven(
    capex: float,
    monthly_profit: float,
    config: Dict[str, Any] = None
) -> int:
    """
    Calculate break-even period in months.

    Args:
        capex: Capital expenditure (initial investment)
        monthly_profit: Monthly profit after operational costs
        config: Optional configuration for additional parameters

    Returns:
        Number of months to break even (rounded up)
    """
    if monthly_profit <= 0:
        return float('inf')  # Never breaks even

    months = capex / monthly_profit
    return int(np.ceil(months))


def calculate_roi(
    initial_investment: float,
    annual_profit: float,
    years: int = 1
) -> float:
    """
    Calculate Return on Investment.

    Args:
        initial_investment: Initial capital invested
        annual_profit: Annual profit
        years: Number of years to calculate over

    Returns:
        ROI as decimal (e.g., 0.25 for 25%)
    """
    if initial_investment == 0:
        return float('inf')

    total_profit = annual_profit * years
    return total_profit / initial_investment


def calculate_payback_period(
    initial_investment: float,
    cashflows: list
) -> float:
    """
    Calculate payback period in years.

    Args:
        initial_investment: Initial investment amount
        cashflows: List of annual cash flows

    Returns:
        Payback period in years
    """
    cumulative = 0
    for year, cf in enumerate(cashflows, 1):
        cumulative += cf
        if cumulative >= initial_investment:
            # Interpolate if needed
            excess = cumulative - initial_investment
            if excess > 0 and year > 1:
                prev_cumulative = cumulative - cf
                fraction = (initial_investment - prev_cumulative) / cf
                return year - 1 + fraction
            return year
    return float('inf')  # Never pays back