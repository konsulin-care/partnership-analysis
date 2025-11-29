"""
TXT Intermediary Module

Generates structured text sections from normalized partnership analysis data
for potential LLM synthesis and narrative generation.
"""

import os
from typing import Dict, Any
from ..config.config_loader import ConfigLoader


def _format_currency(value) -> str:
    """Format numeric values as currency strings."""
    if isinstance(value, (int, float)):
        return f"IDR {value:,}"
    return str(value)


def generate_intermediary_txt(
    normalized_data: Dict[str, Any],
    config: ConfigLoader
) -> str:
    """
    Generate structured TXT sections from normalized data.

    Creates a comprehensive text document with market research findings,
    financial summaries, and partnership narratives suitable for LLM synthesis
    or manual review.

    Args:
        normalized_data: Normalized partnership analysis data
        config: Configuration loader instance

    Returns:
        Path to the generated intermediary TXT file

    Raises:
        ValueError: If normalized data is invalid or missing required sections
        OSError: If file cannot be written
    """
    try:
        if not normalized_data:
            raise ValueError("Normalized data cannot be empty")

        # Validate basic structure
        required_keys = ['metadata', 'organizations', 'partnership_terms', 'financial_data']
        missing_keys = [key for key in required_keys if key not in normalized_data]
        if missing_keys:
            raise ValueError(f"Missing required keys in normalized data: {missing_keys}")

        # Prepare output directory
        output_dir = config.get('output_dir', 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        # Generate text sections
        sections = []

        # Header
        sections.append(_generate_header(normalized_data))

        # Executive Summary
        sections.append(_generate_executive_summary(normalized_data))

        # Market Research Findings
        sections.append(_generate_market_research(normalized_data))

        # Partnership Terms
        sections.append(_generate_partnership_terms(normalized_data))

        # Financial Analysis
        sections.append(_generate_financial_analysis(normalized_data))

        # Quality Flags and Notes
        sections.append(_generate_quality_notes(normalized_data))

        # Combine sections
        content = '\n\n'.join(sections)

        # Write to file
        txt_path = os.path.join(output_dir, 'intermediary.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return txt_path

    except OSError as e:
        raise OSError(f"Failed to write intermediary TXT file: {e}") from e


def _generate_header(data: Dict[str, Any]) -> str:
    """Generate document header section."""
    metadata = data.get('metadata', {})
    doc_id = metadata.get('document_id', 'Unknown')
    generated_at = metadata.get('generated_at', 'Unknown')
    schema_version = metadata.get('schema_version', 'Unknown')

    return f"""PARTNERSHIP ANALYSIS INTERMEDIARY DOCUMENT

Document ID: {doc_id}
Generated At: {generated_at}
Schema Version: {schema_version}

This document contains structured text sections derived from normalized partnership analysis data.
It is designed for LLM synthesis, narrative generation, or manual review."""


def _generate_executive_summary(data: Dict[str, Any]) -> str:
    """Generate executive summary section."""
    orgs = data.get('organizations', [])
    partner_name = "Unknown Partner"
    for org in orgs:
        if org.get('role') == 'partner':
            partner_name = org.get('name', 'Unknown Partner')
            break

    financial = data.get('financial_data', {})
    scenarios = financial.get('scenarios', [])
    hub_scenario = next((s for s in scenarios if s.get('name') == 'hub'), {})
    standalone_scenario = next((s for s in scenarios if s.get('name') == 'standalone'), {})

    hub_breakeven = hub_scenario.get('breakeven_months', 'N/A')
    standalone_breakeven = standalone_scenario.get('breakeven_months', 'N/A')

    return f"""EXECUTIVE SUMMARY

This analysis evaluates the partnership opportunity for {partner_name} in the wellness hub model.

Key Findings:
- Hub Model Breakeven: {hub_breakeven} months
- Standalone Model Breakeven: {standalone_breakeven} months

The wellness hub model offers shared infrastructure, marketing synergies, and operational efficiencies
compared to standalone clinic operations."""


def _generate_market_research(data: Dict[str, Any]) -> str:
    """Generate market research findings section."""
    research = data.get('research_data', {})
    benchmarks = research.get('market_benchmarks', [])

    if not benchmarks:
        return """MARKET RESEARCH FINDINGS

No market research data available in the normalized dataset.
Research benchmarks should be extracted from web search results and included in the research_data section."""

    findings = []
    for benchmark in benchmarks:
        category = benchmark.get('category', 'Unknown')
        value = benchmark.get('value', 'N/A')
        unit = benchmark.get('unit', '')
        source = benchmark.get('source_citation', 'Unknown')
        confidence = benchmark.get('confidence', 0)

        findings.append(f"- {category}: {value} {unit} (Source: {source}, Confidence: {confidence:.2f})")

    return f"""MARKET RESEARCH FINDINGS

The following benchmarks were extracted from recent market research:

{chr(10).join(findings)}

These benchmarks inform the financial modeling and scenario analysis presented in subsequent sections."""


def _generate_partnership_terms(data: Dict[str, Any]) -> str:
    """Generate partnership terms section."""
    terms = data.get('partnership_terms', {})

    revenue_share = terms.get('revenue_share_pct', 'N/A')
    min_fee = terms.get('minimum_monthly_fee_idr', 'N/A')
    capex = terms.get('capex_investment_idr', 'N/A')
    hub_contribution = terms.get('capex_hub_contribution_idr', 'N/A')
    commitment = terms.get('commitment_years', 'N/A')
    space = terms.get('space_sqm', 'N/A')
    timeline = terms.get('launch_timeline_days', 'N/A')

    return f"""PARTNERSHIP TERMS

Revenue Sharing: {revenue_share}% of monthly revenue
Minimum Monthly Fee: {_format_currency(min_fee)}
CAPEX Investment (Tenant): {_format_currency(capex)}
CAPEX Contribution (Hub): {_format_currency(hub_contribution)}
Commitment Period: {commitment} years
Space Allocation: {space} sqm
Launch Timeline: {timeline} days

These terms define the financial and operational commitments for the partnership."""


def _generate_financial_analysis(data: Dict[str, Any]) -> str:
    """Generate financial analysis section."""
    financial = data.get('financial_data', {})
    scenarios = financial.get('scenarios', [])

    if not scenarios:
        return """FINANCIAL ANALYSIS

No financial scenarios available in the normalized dataset.
Financial calculations should include revenue projections, cost breakdowns, and breakeven analysis."""

    analysis = []
    for scenario in scenarios:
        name = scenario.get('name', 'Unknown').title()
        revenue = scenario.get('monthly_revenue_idr', 0)
        costs = scenario.get('monthly_costs', {})
        profit = scenario.get('monthly_profit_idr', 0)
        breakeven = scenario.get('breakeven_months', 'N/A')

        total_costs = sum(costs.values())

        analysis.append(f"""{name} Scenario:
- Monthly Revenue: {_format_currency(revenue)}
- Monthly Costs: {_format_currency(total_costs)}
- Monthly Profit: {_format_currency(profit)}
- Breakeven Timeline: {breakeven} months""")

    year1_revenue = financial.get('year_1_revenue_idr', 'N/A')
    year3_savings = financial.get('year_3_cumulative_savings_idr', 'N/A')
    discount_rate = financial.get('npv_discount_rate', 'N/A')

    summary = f"""
Year 1 Revenue Projection: {_format_currency(year1_revenue)}
Year 3 Cumulative Savings: {_format_currency(year3_savings)}
NPV Discount Rate: {discount_rate}"""

    return f"""FINANCIAL ANALYSIS

Detailed financial projections for different business models:

{chr(10).join(analysis)}

{summary}

These projections are based on market benchmarks, operational assumptions, and partnership terms."""


def _generate_quality_notes(data: Dict[str, Any]) -> str:
    """Generate quality flags and notes section."""
    flags = data.get('quality_flags', {})
    missing = flags.get('missing_data_fields', [])
    low_conf = flags.get('low_confidence_entities', [])
    inconsistencies = flags.get('data_inconsistencies', [])

    notes = []

    if missing:
        notes.append(f"Missing Data Fields: {', '.join(missing)}")

    if low_conf:
        notes.append(f"Low Confidence Entities: {', '.join(low_conf)}")

    if inconsistencies:
        notes.append(f"Data Inconsistencies: {', '.join(inconsistencies)}")

    if not notes:
        notes.append("No quality issues identified in the normalized data.")

    return f"""QUALITY FLAGS AND NOTES

{chr(10).join(notes)}

This section highlights potential data quality issues that may affect the analysis reliability."""