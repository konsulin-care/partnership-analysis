"""
Scenario Builder Module

Generates sensitivity analysis tables and scenario comparisons for financial modeling.
"""

from typing import Dict, List, Any
from .financial_models import calculate_operational_costs, calculate_revenue_share


def generate_sensitivity_table(
    base_revenue: float,
    variance_range: List[float],
    model_type: str,
    config: Dict[str, Any]
):
    """
    Generate sensitivity analysis table showing impact of revenue variations.

    Args:
        base_revenue: Base monthly revenue
        variance_range: List of variance percentages (e.g., [-0.2, -0.1, 0, 0.1, 0.2])
        model_type: Business model type ('standalone' or 'hub')
        config: Configuration parameters

    Returns:
        DataFrame with sensitivity analysis
    """
    import pandas as pd

    results = []

    for variance in variance_range:
        revenue = base_revenue * (1 + variance)
        costs = calculate_operational_costs(revenue, model_type, config)
        total_costs = costs['total_operational_costs']
        profit = revenue - total_costs

        results.append({
            'variance_pct': variance * 100,
            'revenue': revenue,
            'total_costs': total_costs,
            'profit': profit,
            'profit_margin': profit / revenue if revenue > 0 else 0,
        })

    return pd.DataFrame(results)


def generate_scenario_comparison(
    scenarios: Dict[str, Dict[str, Any]],
    config: Dict[str, Any]
):
    """
    Compare different business scenarios.

    Args:
        scenarios: Dict of scenario_name -> scenario_params
        config: Configuration parameters

    Returns:
        DataFrame comparing scenarios
    """
    import pandas as pd

    results = []

    for scenario_name, params in scenarios.items():
        revenue = params['revenue']
        model_type = params['model_type']
        capex = params.get('capex', 0)

        costs = calculate_operational_costs(revenue, model_type, config)
        total_costs = costs['total_operational_costs']
        profit = revenue - total_costs

        results.append({
            'scenario': scenario_name,
            'model_type': model_type,
            'revenue': revenue,
            'total_costs': total_costs,
            'profit': profit,
            'profit_margin': profit / revenue if revenue > 0 else 0,
            'capex': capex,
        })

    return pd.DataFrame(results)