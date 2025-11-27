"""
Financial Calculator Module

This module provides deterministic financial computations for partnership analysis,
including cost-benefit scenarios, break-even analysis, and sensitivity modeling.
"""

from .financial_models import (
    calculate_operational_costs,
    calculate_revenue_share,
    calculate_npv,
)
from .breakeven_analyzer import calculate_breakeven
from .scenario_builder import generate_sensitivity_table
from .validators import validate_calculations

__all__ = [
    "calculate_operational_costs",
    "calculate_revenue_share",
    "calculate_npv",
    "calculate_breakeven",
    "generate_sensitivity_table",
    "validate_calculations",
]