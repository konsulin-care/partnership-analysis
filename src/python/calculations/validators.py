"""
Validators Module

Provides mathematical validation and sanity checks for financial calculations.
"""

import math
from typing import Dict, List, Tuple, Any


def validate_calculations(results: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate financial calculation results for mathematical consistency.

    Args:
        results: Dictionary of calculation results

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check for NaN or infinite values
    for key, value in results.items():
        if isinstance(value, (int, float)):
            if math.isnan(value):
                errors.append(f"{key}: NaN value detected")
            elif math.isinf(value):
                errors.append(f"{key}: Infinite value detected")

    # Check profit calculations
    if 'profit' in results and 'revenue' in results and 'total_costs' in results:
        expected_profit = results['revenue'] - results['total_costs']
        if not math.isclose(results['profit'], expected_profit, rel_tol=1e-6):
            errors.append(f"Profit calculation mismatch: expected {expected_profit}, got {results['profit']}")

    # Check break-even logic
    if 'breakeven_months' in results and 'capex' in results and 'monthly_profit' in results:
        if results['monthly_profit'] > 0:
            expected_months = math.ceil(results['capex'] / results['monthly_profit'])
            if results['breakeven_months'] != expected_months:
                errors.append(f"Break-even calculation mismatch: expected {expected_months}, got {results['breakeven_months']}")

    # Check NPV consistency
    if 'npv' in results and 'cashflows' in results and 'discount_rate' in results:
        # Recalculate NPV
        cashflows = results['cashflows']
        discount_rate = results['discount_rate']
        calculated_npv = sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cashflows))
        if not math.isclose(results['npv'], calculated_npv, rel_tol=1e-6):
            errors.append(f"NPV calculation mismatch: expected {calculated_npv}, got {results['npv']}")

    # Check revenue share
    if 'revenue_share' in results and 'revenue' in results and 'share_pct' in results:
        expected_share = results['revenue'] * results['share_pct']
        if 'minimum' in results:
            expected_share = max(expected_share, results['minimum'])
        if not math.isclose(results['revenue_share'], expected_share, rel_tol=1e-6):
            errors.append(f"Revenue share calculation mismatch: expected {expected_share}, got {results['revenue_share']}")

    # Business logic checks
    if 'profit_margin' in results:
        if results['profit_margin'] < -1.0 or results['profit_margin'] > 1.0:
            errors.append(f"Profit margin out of reasonable range: {results['profit_margin']}")

    if 'roi' in results and isinstance(results['roi'], (int, float)):
        if results['roi'] < -2.0:  # Allow some negative ROI but flag extreme
            errors.append(f"ROI seems unreasonably negative: {results['roi']}")

    return len(errors) == 0, errors


def validate_inputs(**kwargs) -> Tuple[bool, List[str]]:
    """
    Validate input parameters for calculations.

    Args:
        kwargs: Input parameters

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    for key, value in kwargs.items():
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                errors.append(f"{key}: Invalid numeric value")
            elif value < 0 and key in ['revenue', 'profit', 'investment']:
                errors.append(f"{key}: Negative value not allowed")
        elif isinstance(value, list):
            if not value:
                errors.append(f"{key}: Empty list not allowed")

    return len(errors) == 0, errors