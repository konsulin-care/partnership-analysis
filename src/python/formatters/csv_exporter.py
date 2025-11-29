"""
CSV Exporter Module

Exports financial scenario comparison data to CSV format for spreadsheet analysis.
Creates scenario comparison tables with metrics across standalone and hub scenarios.
"""

import os
import pandas as pd
from typing import Dict, Any, List
from ..config.config_loader import ConfigLoader


def export_financial_tables_to_csv(
    normalized_data: Dict[str, Any],
    config: ConfigLoader
) -> List[str]:
    """
    Export financial scenario comparison table to CSV.

    Creates a scenario comparison table with metrics across standalone/hub scenarios,
    including calculated advantages and formatted values.

    Args:
        normalized_data: Normalized partnership analysis data
        config: Configuration loader instance

    Returns:
        List of exported CSV file paths

    Raises:
        ValueError: If required financial data is missing
        OSError: If file cannot be written
    """
    try:
        # Extract financial data
        financial_data = normalized_data.get('financial_data', {})
        scenarios = financial_data.get('scenarios', [])
        partnership_terms = normalized_data.get('partnership_terms', {})

        if not scenarios:
            raise ValueError("No financial scenarios found in normalized data")

        # Find standalone and hub scenarios
        standalone = None
        hub = None
        for scenario in scenarios:
            if scenario.get('name') == 'standalone':
                standalone = scenario
            elif scenario.get('name') == 'hub':
                hub = scenario

        if not standalone or not hub:
            raise ValueError("Both standalone and hub scenarios required for comparison")

        # Calculate metrics
        metrics = _calculate_scenario_metrics(standalone, hub, partnership_terms, config)

        # Create DataFrame
        df = pd.DataFrame(metrics)

        # Format values
        df = _format_dataframe_values(df, config)

        # Export to CSV
        output_dir = config.get('output_dir', 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        csv_path = os.path.join(output_dir, 'scenario_comparison.csv')
        df.to_csv(csv_path, index=False)

        return [csv_path]

    except ValueError:
        raise
    except Exception as e:
        raise OSError(f"Failed to export CSV: {e}") from e


def _calculate_scenario_metrics(
    standalone: Dict[str, Any],
    hub: Dict[str, Any],
    partnership_terms: Dict[str, Any],
    config: ConfigLoader
) -> List[Dict[str, Any]]:
    """
    Calculate scenario comparison metrics.

    Args:
        standalone: Standalone scenario data
        hub: Hub scenario data
        partnership_terms: Partnership terms data
        config: Configuration loader

    Returns:
        List of metric dictionaries for DataFrame
    """
    # Initial Investment
    standalone_capex = partnership_terms.get('capex_investment_idr', 0)
    hub_capex = standalone_capex - partnership_terms.get('capex_hub_contribution_idr', 0)

    capex_advantage = _calculate_advantage(standalone_capex, hub_capex, lower_better=True)

    # Break-even Timeline
    standalone_breakeven = standalone.get('breakeven_months', 0)
    hub_breakeven = hub.get('breakeven_months', 0)

    breakeven_advantage = _calculate_advantage(standalone_breakeven, hub_breakeven, lower_better=True)

    # Monthly Operating Cost
    standalone_monthly_cost = sum(standalone.get('monthly_costs', {}).values())
    hub_monthly_cost = sum(hub.get('monthly_costs', {}).values())

    cost_advantage = _calculate_advantage(standalone_monthly_cost, hub_monthly_cost, lower_better=True)

    # Year 1 Profit
    standalone_profit = standalone.get('annual_profit_idr', 0)
    hub_profit = hub.get('annual_profit_idr', 0)

    profit_advantage = _calculate_advantage(standalone_profit, hub_profit, lower_better=False)

    return [
        {
            'Metric': 'Initial Investment',
            'Standalone': standalone_capex,
            'Hub': hub_capex,
            'Advantage': capex_advantage
        },
        {
            'Metric': 'Break-Even Timeline',
            'Standalone': standalone_breakeven,
            'Hub': hub_breakeven,
            'Advantage': breakeven_advantage
        },
        {
            'Metric': 'Monthly Operating Cost',
            'Standalone': standalone_monthly_cost,
            'Hub': hub_monthly_cost,
            'Advantage': cost_advantage
        },
        {
            'Metric': 'Year 1 Profit',
            'Standalone': standalone_profit,
            'Hub': hub_profit,
            'Advantage': profit_advantage
        }
    ]


def _calculate_advantage(standalone_value: float, hub_value: float, lower_better: bool) -> str:
    """
    Calculate advantage percentage.

    Args:
        standalone_value: Standalone scenario value
        hub_value: Hub scenario value
        lower_better: Whether lower values are better

    Returns:
        Formatted advantage percentage string
    """
    if standalone_value == 0:
        return "N/A"

    if lower_better:
        advantage = (standalone_value - hub_value) / standalone_value * 100
    else:
        advantage = (hub_value - standalone_value) / standalone_value * 100

    return f"{advantage:.1f}%"


def _format_dataframe_values(df: pd.DataFrame, config: ConfigLoader) -> pd.DataFrame:
    """
    Format DataFrame values for display.

    Args:
        df: Raw metrics DataFrame
        config: Configuration loader

    Returns:
        Formatted DataFrame
    """
    currency_format = config.get('currency_format', 'IDR {:,.0f}')
    unit_format = config.get('unit_format', '{:.1f}')

    formatted_df = df.copy()

    # Format currency columns
    currency_columns = ['Standalone', 'Hub']
    for col in currency_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda x: currency_format.format(x) if isinstance(x, (int, float)) else str(x)
            )

    # Format unit columns (Advantage is already formatted)
    unit_columns = ['Advantage']
    for col in unit_columns:
        if col in formatted_df.columns:
            # Advantage is already a string with %
            pass

    return formatted_df