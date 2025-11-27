"""
Financial Models Module

Provides core deterministic financial calculations for cost-benefit analysis,
revenue sharing, and net present value computations.
"""

import numpy as np
from typing import Dict, List, Any
from ..config.config_loader import ConfigLoader


def calculate_operational_costs(
    revenue: float,
    model_type: str,
    config: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate operational costs based on revenue and business model type.

    Args:
        revenue: Monthly revenue in local currency
        model_type: 'standalone' or 'hub'
        config: Configuration dictionary with cost parameters

    Returns:
        Dictionary of operational costs
    """
    if model_type == 'standalone':
        # Fixed costs based on Indonesian clinic benchmarks
        rent = config.get('standalone_rent_monthly', 20_833_333)  # IDR
        staff = config.get('standalone_staff_monthly', 30_500_000)  # IDR
        utilities = config.get('standalone_utilities_monthly', 5_000_000)  # IDR
        marketing = revenue * config.get('marketing_percentage', 0.05)  # 5% of revenue
        supplies = revenue * config.get('supplies_percentage', 0.10)  # 10% of revenue

        total_costs = rent + staff + utilities + marketing + supplies

    elif model_type == 'hub':
        # Hub model: shared costs
        revenue_share = revenue * config.get('hub_revenue_share_pct', 0.12)  # 12% of revenue
        staff_share = config.get('hub_staff_share_monthly', 4_916_750)  # IDR
        utilities_share = config.get('hub_utilities_share_monthly', 833_333)  # IDR
        marketing_share = revenue * config.get('hub_marketing_share_pct', 0.02)  # 2% of revenue

        total_costs = revenue_share + staff_share + utilities_share + marketing_share

    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    return {
        'total_operational_costs': total_costs,
        'rent': rent if model_type == 'standalone' else 0,
        'staff': staff if model_type == 'standalone' else staff_share,
        'utilities': utilities if model_type == 'standalone' else utilities_share,
        'marketing': marketing if model_type == 'standalone' else marketing_share,
        'supplies': supplies if model_type == 'standalone' else 0,
        'revenue_share': 0 if model_type == 'standalone' else revenue_share,
    }


def calculate_revenue_share(
    revenue: float,
    share_pct: float,
    minimum: float = 0
) -> float:
    """
    Calculate revenue share amount with optional minimum guarantee.

    Args:
        revenue: Total revenue
        share_pct: Revenue share percentage (0.0 to 1.0)
        minimum: Minimum guaranteed amount

    Returns:
        Revenue share amount
    """
    share_amount = revenue * share_pct
    return max(share_amount, minimum)


def calculate_npv(
    cashflows: List[float],
    discount_rate: float
) -> float:
    """
    Calculate Net Present Value of cash flows.

    Args:
        cashflows: List of cash flows (first element is initial investment, negative)
        discount_rate: Annual discount rate (0.0 to 1.0)

    Returns:
        NPV value
    """
    if not cashflows:
        return 0.0

    npv = 0.0
    for t, cf in enumerate(cashflows):
        npv += cf / (1 + discount_rate) ** t

    return npv