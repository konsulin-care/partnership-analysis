"""
Carbone JSON Builder Module

Transforms normalized partnership analysis data into Carbone SDK compatible JSON
payload for PDF generation, including calculated advantages and formatted tables.
"""

import os
from typing import Dict, Any, List
from ..config.config_loader import ConfigLoader


def generate_carbone_json(
    normalized_data: Dict[str, Any],
    config: ConfigLoader
) -> Dict[str, Any]:
    """
    Generate Carbone-compatible JSON payload from normalized data.

    Transforms partnership analysis data into the structured JSON format required
    by Carbone SDK for PDF generation, including calculated financial advantages
    and formatted data tables.

    Args:
        normalized_data: Normalized partnership analysis data
        config: Configuration loader instance

    Returns:
        Carbone-compatible JSON payload dictionary

    Raises:
        ValueError: If required data is missing or invalid
    """
    try:
        if not normalized_data:
            raise ValueError("Normalized data is required for Carbone JSON generation")

        # Validate required keys
        required_keys = ['metadata', 'organizations', 'partnership_terms', 'financial_data']
        missing_keys = [key for key in required_keys if key not in normalized_data]
        if missing_keys:
            raise ValueError(f"Missing required keys in normalized data: {missing_keys}")

        # Extract key data sections
        metadata = normalized_data.get('metadata', {})
        organizations = normalized_data.get('organizations', [])
        partnership_terms = normalized_data.get('partnership_terms', {})
        financial_data = normalized_data.get('financial_data', {})
        research_data = normalized_data.get('research_data', {})

        # Build Carbone payload structure
        carbone_payload = {
            "data": {
                "document": _build_document_section(metadata, organizations),
                "executive_summary": _build_executive_summary(financial_data, partnership_terms),
                "partnership_overview": _build_partnership_overview(organizations, partnership_terms),
                "financial_analysis": _build_financial_analysis(financial_data, partnership_terms),
                "market_research": _build_market_research(research_data),
                "recommendations": _build_recommendations(financial_data),
                "references": _build_references(research_data)
            },
            "template": config.get('carbone_template_id', 'partnership_report_v1'),
            "options": _build_carbone_options(config)
        }

        return carbone_payload

    except Exception as e:
        raise ValueError(f"Failed to generate Carbone JSON: {e}") from e


def _build_document_section(metadata: Dict[str, Any], organizations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build document metadata section."""
    # Extract title from organizations
    tenant_name = ""
    hub_name = ""
    for org in organizations:
        if org.get('role') == 'tenant':
            tenant_name = org.get('name', '')
        elif org.get('role') == 'hub_operator':
            hub_name = org.get('name', '')

    title = f"Partnership Analysis: {hub_name} x {tenant_name}" if hub_name and tenant_name else "Partnership Analysis Report"

    return {
        "title": title,
        "date": metadata.get('generated_at', '').split('T')[0] if metadata.get('generated_at') else "2025-11-28",
        "author": hub_name or "Analysis Team",
        "contact": _extract_contact_email(organizations)
    }


def _extract_contact_email(organizations: List[Dict[str, Any]]) -> str:
    """Extract primary contact email from organizations."""
    for org in organizations:
        contact = org.get('contact', {})
        email = contact.get('email')
        if email:
            return email
    return "contact@example.com"


def _build_executive_summary(financial_data: Dict[str, Any], partnership_terms: Dict[str, Any]) -> Dict[str, Any]:
    """Build executive summary with key findings."""
    scenarios = financial_data.get('scenarios', [])
    standalone = next((s for s in scenarios if s.get('name') == 'standalone'), {})
    hub = next((s for s in scenarios if s.get('name') == 'hub'), {})

    # Calculate key advantages
    capex_standalone = partnership_terms.get('capex_investment_idr', 0)
    capex_hub = capex_standalone - partnership_terms.get('capex_hub_contribution_idr', 0)
    capex_reduction = (capex_standalone - capex_hub) / capex_standalone * 100 if capex_standalone > 0 else 0

    breakeven_standalone = standalone.get('breakeven_months', 0)
    breakeven_hub = hub.get('breakeven_months', 0)
    breakeven_improvement = (breakeven_standalone - breakeven_hub) / breakeven_standalone * 100 if breakeven_standalone > 0 else 0

    savings_3yr = financial_data.get('year_3_cumulative_savings_idr', 0)

    return {
        "headline": "Partnership Model Delivers Superior Financial Outcomes",
        "key_findings": [
            f"{capex_reduction:.1f}% reduction in initial capital requirements",
            f"{breakeven_improvement:.1f} months faster break-even timeline",
            f"IDR {savings_3yr:,.0f} in cumulative savings over three years"
        ]
    }


def _build_partnership_overview(organizations: List[Dict[str, Any]], partnership_terms: Dict[str, Any]) -> Dict[str, Any]:
    """Build partnership overview section."""
    parties = []
    for org in organizations:
        party = {
            "name": org.get('name', ''),
            "role": _format_role(org.get('role', '')),
            "location": f"{org.get('location', {}).get('city', '')}, {org.get('location', {}).get('country', '')}".strip(', ')
        }
        parties.append(party)

    terms = {
        "revenue_share_pct": partnership_terms.get('revenue_share_pct', 0),
        "space_sqm": partnership_terms.get('space_sqm', 0),
        "commitment_years": partnership_terms.get('commitment_years', 0),
        "launch_timeline_days": partnership_terms.get('launch_timeline_days', 0)
    }

    return {
        "parties": parties,
        "terms": terms
    }


def _format_role(role: str) -> str:
    """Format role string for display."""
    role_map = {
        'hub_operator': 'Hub Operator',
        'tenant': 'Tenant'
    }
    return role_map.get(role, role.replace('_', ' ').title())


def _build_financial_analysis(financial_data: Dict[str, Any], partnership_terms: Dict[str, Any]) -> Dict[str, Any]:
    """Build financial analysis section with tables."""
    scenarios = financial_data.get('scenarios', [])
    standalone = next((s for s in scenarios if s.get('name') == 'standalone'), {})
    hub = next((s for s in scenarios if s.get('name') == 'hub'), {})

    # Scenario comparison table
    comparison_table = _build_scenario_comparison_table(standalone, hub, partnership_terms)

    # Three-year projection table
    projection_table = _build_three_year_projection_table(financial_data)

    return {
        "sections": [
            {
                "title": "Scenario Comparison",
                "tables": [comparison_table]
            },
            {
                "title": "Three-Year Projection",
                "tables": [projection_table]
            }
        ]
    }


def _build_scenario_comparison_table(standalone: Dict[str, Any], hub: Dict[str, Any], partnership_terms: Dict[str, Any]) -> Dict[str, Any]:
    """Build scenario comparison table."""
    # Calculate values
    capex_standalone = partnership_terms.get('capex_investment_idr', 0)
    capex_hub = capex_standalone - partnership_terms.get('capex_hub_contribution_idr', 0)
    capex_advantage = f"{(capex_standalone - capex_hub) / capex_standalone * 100:.1f}%" if capex_standalone > 0 else "N/A"

    breakeven_standalone = standalone.get('breakeven_months', 0)
    breakeven_hub = hub.get('breakeven_months', 0)
    breakeven_advantage = f"{(breakeven_standalone - breakeven_hub) / breakeven_standalone * 100:.1f}%" if breakeven_standalone > 0 else "N/A"

    cost_standalone = sum(standalone.get('monthly_costs', {}).values())
    cost_hub = sum(hub.get('monthly_costs', {}).values())
    cost_advantage = f"{(cost_standalone - cost_hub) / cost_standalone * 100:.1f}%" if cost_standalone > 0 else "N/A"

    profit_standalone = standalone.get('annual_profit_idr', 0)
    profit_hub = hub.get('annual_profit_idr', 0)
    profit_advantage = f"{(profit_hub - profit_standalone) / profit_standalone * 100:.1f}%" if profit_standalone > 0 else "N/A"

    return {
        "header": ["Metric", "Standalone", "Hub", "Advantage"],
        "rows": [
            ["Initial Investment", f"IDR {capex_standalone:,.0f}", f"IDR {capex_hub:,.0f}", capex_advantage],
            ["Break-Even Timeline", f"{breakeven_standalone:.1f} months", f"{breakeven_hub:.1f} months", breakeven_advantage],
            ["Monthly Operating Cost", f"IDR {cost_standalone:,.0f}", f"IDR {cost_hub:,.0f}", cost_advantage],
            ["Year 1 Profit", f"IDR {profit_standalone:,.0f}", f"IDR {profit_hub:,.0f}", profit_advantage]
        ]
    }


def _build_three_year_projection_table(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build three-year savings projection table."""
    # This is a simplified projection - in real implementation, calculate year-by-year
    year_1_savings = financial_data.get('year_1_revenue_idr', 0) * 0.1  # Placeholder calculation
    year_2_savings = year_1_savings * 1.05  # 5% growth
    year_3_savings = year_2_savings * 1.05
    total_savings = year_1_savings + year_2_savings + year_3_savings

    return {
        "header": ["Year", "Annual Savings"],
        "rows": [
            ["Year 1", f"IDR {year_1_savings:,.0f}"],
            ["Year 2", f"IDR {year_2_savings:,.0f}"],
            ["Year 3", f"IDR {year_3_savings:,.0f}"],
            ["Total 3-Year", f"IDR {total_savings:,.0f}"]
        ]
    }


def _build_market_research(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build market research section."""
    benchmarks = research_data.get('market_benchmarks', [])

    benchmark_items = []
    for benchmark in benchmarks:
        item = {
            "category": benchmark.get('category', '').replace('_', ' ').title(),
            "value": _format_benchmark_value(benchmark),
            "source": benchmark.get('source_citation', 'Research Data')
        }
        benchmark_items.append(item)

    return {
        "sections": [
            {
                "title": "Market Benchmarks",
                "content": "Analysis grounded in current market data:",
                "benchmarks": benchmark_items
            }
        ]
    }


def _format_benchmark_value(benchmark: Dict[str, Any]) -> str:
    """Format benchmark value for display."""
    value = benchmark.get('value', '')
    unit = benchmark.get('unit', '')

    if isinstance(value, (int, float)):
        if 'idr' in unit.lower():
            return f"IDR {value:,.0f}"
        elif 'pct' in unit.lower() or 'rate' in unit.lower():
            return f"{value * 100:.1f}%"
        else:
            return str(value)
    return str(value)


def _build_recommendations(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build recommendations section."""
    # Simple recommendation based on financial data
    scenarios = financial_data.get('scenarios', [])
    hub_scenario = next((s for s in scenarios if s.get('name') == 'hub'), {})

    if hub_scenario.get('breakeven_months', 999) < 12:  # If break-even within a year
        primary_rec = "Proceed with Wellness Hub partnership model"
        rationale = "Superior financial outcomes with lower capital exposure and operational complexity"
    else:
        primary_rec = "Consider phased implementation approach"
        rationale = "Evaluate operational metrics before full commitment"

    return {
        "primary": primary_rec,
        "rationale": rationale,
        "action_items": [
            "Execute partnership agreement with specified commitment period",
            "Coordinate tenant build-out and equipment procurement",
            "Launch marketing and patient acquisition campaign",
            "Establish integrated booking and payment systems"
        ]
    }


def _build_references(research_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build references section."""
    benchmarks = research_data.get('market_benchmarks', [])

    references = []
    for i, benchmark in enumerate(benchmarks, 1):
        ref = {
            "id": f"[{i}]",
            "text": f"{benchmark.get('source_citation', 'Research Data')}. {benchmark.get('research_date', '2025')[:4]}. Market analysis data."
        }
        references.append(ref)

    return references


def _build_carbone_options(config: ConfigLoader) -> Dict[str, Any]:
    """Build Carbone rendering options."""
    return {
        "language": config.get('report_language', 'en'),
        "format": "pdf",
        "margins": {
            "top": config.get('pdf_margin_top', 20),
            "bottom": config.get('pdf_margin_bottom', 20),
            "left": config.get('pdf_margin_left', 15),
            "right": config.get('pdf_margin_right', 15)
        }
    }