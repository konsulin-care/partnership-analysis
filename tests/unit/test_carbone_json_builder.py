"""
Unit tests for carbone_json_builder.py
"""

import pytest
from unittest.mock import Mock
from src.python.formatters.carbone_json_builder import (
    generate_carbone_json,
    _build_document_section,
    _build_executive_summary,
    _build_partnership_overview,
    _build_financial_analysis,
    _build_market_research,
    _build_recommendations,
    _build_references,
    _build_carbone_options,
    _format_role,
    _extract_contact_email,
    _build_scenario_comparison_table,
    _build_three_year_projection_table,
    _format_benchmark_value,
)


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'carbone_template_id': 'test_template_v1',
        'report_language': 'en',
        'pdf_margin_top': 20,
        'pdf_margin_bottom': 20,
        'pdf_margin_left': 15,
        'pdf_margin_right': 15
    }.get(key, default)
    return config


@pytest.fixture
def mock_normalized_data():
    """Mock normalized data with all required sections."""
    return {
        'metadata': {
            'generated_at': '2025-11-28T10:00:00Z'
        },
        'organizations': [
            {
                'name': 'Test Hub',
                'role': 'hub_operator',
                'location': {'city': 'Jakarta', 'country': 'Indonesia'},
                'contact': {'email': 'hub@test.com'}
            },
            {
                'name': 'Test Clinic',
                'role': 'tenant',
                'location': {'city': 'Jakarta', 'country': 'Indonesia'},
                'contact': {'email': 'clinic@test.com'}
            }
        ],
        'partnership_terms': {
            'revenue_share_pct': 12.5,
            'capex_investment_idr': 200000000,
            'capex_hub_contribution_idr': 50000000,
            'space_sqm': 150,
            'commitment_years': 3,
            'launch_timeline_days': 90
        },
        'financial_data': {
            'scenarios': [
                {
                    'name': 'standalone',
                    'breakeven_months': 24,
                    'monthly_costs': {'rent_idr': 20000000, 'staff_idr': 30000000},
                    'annual_profit_idr': 200000000
                },
                {
                    'name': 'hub',
                    'breakeven_months': 12,
                    'monthly_costs': {'rent_idr': 0, 'staff_idr': 25000000},
                    'annual_profit_idr': 250000000
                }
            ],
            'year_1_revenue_idr': 285000000,
            'year_3_cumulative_savings_idr': 500000000
        },
        'research_data': {
            'market_benchmarks': [
                {
                    'category': 'hair_transplant_pricing',
                    'value': 30000000,
                    'unit': 'idr',
                    'source_citation': 'Market Report 2025'
                }
            ]
        }
    }


def test_generate_carbone_json_success(mock_normalized_data, mock_config):
    """Test successful Carbone JSON generation."""
    result = generate_carbone_json(mock_normalized_data, mock_config)

    assert isinstance(result, dict)
    assert 'data' in result
    assert 'template' in result
    assert 'options' in result

    assert result['template'] == 'test_template_v1'

    data = result['data']
    assert 'document' in data
    assert 'executive_summary' in data
    assert 'partnership_overview' in data
    assert 'financial_analysis' in data
    assert 'market_research' in data
    assert 'recommendations' in data
    assert 'references' in data


def test_generate_carbone_json_missing_data(mock_config):
    """Test Carbone JSON generation fails with missing data."""
    incomplete_data = {
        'metadata': {},
        # Missing other required sections
    }

    with pytest.raises(ValueError, match="Failed to generate Carbone JSON"):
        generate_carbone_json(incomplete_data, mock_config)


def test_build_document_section(mock_normalized_data):
    """Test document section building."""
    metadata = mock_normalized_data['metadata']
    organizations = mock_normalized_data['organizations']

    result = _build_document_section(metadata, organizations)

    assert result['title'] == 'Partnership Analysis: Test Hub x Test Clinic'
    assert result['date'] == '2025-11-28'
    assert result['author'] == 'Test Hub'
    assert result['contact'] == 'hub@test.com'


def test_build_document_section_no_hub(mock_normalized_data):
    """Test document section with no hub operator."""
    metadata = mock_normalized_data['metadata']
    organizations = [{'name': 'Clinic Only', 'role': 'tenant'}]

    result = _build_document_section(metadata, organizations)

    assert result['title'] == 'Partnership Analysis Report'
    assert result['author'] == 'Analysis Team'
    assert result['contact'] == 'contact@example.com'


def test_build_executive_summary(mock_normalized_data):
    """Test executive summary building."""
    financial_data = mock_normalized_data['financial_data']
    partnership_terms = mock_normalized_data['partnership_terms']

    result = _build_executive_summary(financial_data, partnership_terms)

    assert 'headline' in result
    assert 'key_findings' in result
    assert len(result['key_findings']) == 3
    assert '25.0% reduction' in result['key_findings'][0]
    assert '50.0 months faster' in result['key_findings'][1]


def test_build_partnership_overview(mock_normalized_data):
    """Test partnership overview building."""
    organizations = mock_normalized_data['organizations']
    partnership_terms = mock_normalized_data['partnership_terms']

    result = _build_partnership_overview(organizations, partnership_terms)

    assert 'parties' in result
    assert 'terms' in result
    assert len(result['parties']) == 2
    assert result['parties'][0]['name'] == 'Test Hub'
    assert result['parties'][0]['role'] == 'Hub Operator'
    assert result['terms']['revenue_share_pct'] == 12.5


def test_build_financial_analysis(mock_normalized_data):
    """Test financial analysis building."""
    financial_data = mock_normalized_data['financial_data']
    partnership_terms = mock_normalized_data['partnership_terms']

    result = _build_financial_analysis(financial_data, partnership_terms)

    assert 'sections' in result
    assert len(result['sections']) == 2
    assert result['sections'][0]['title'] == 'Scenario Comparison'
    assert result['sections'][1]['title'] == 'Three-Year Projection'


def test_build_market_research(mock_normalized_data):
    """Test market research building."""
    research_data = mock_normalized_data['research_data']

    result = _build_market_research(research_data)

    assert 'sections' in result
    assert len(result['sections']) == 1
    assert result['sections'][0]['title'] == 'Market Benchmarks'
    assert len(result['sections'][0]['benchmarks']) == 1
    assert result['sections'][0]['benchmarks'][0]['category'] == 'Hair Transplant Pricing'


def test_build_recommendations(mock_normalized_data):
    """Test recommendations building."""
    financial_data = mock_normalized_data['financial_data']

    result = _build_recommendations(financial_data)

    assert 'primary' in result
    assert 'rationale' in result
    assert 'action_items' in result
    assert len(result['action_items']) == 4


def test_build_references(mock_normalized_data):
    """Test references building."""
    research_data = mock_normalized_data['research_data']

    result = _build_references(research_data)

    assert len(result) == 1
    assert result[0]['id'] == '[1]'
    assert 'Market Report 2025' in result[0]['text']


def test_build_carbone_options(mock_config):
    """Test Carbone options building."""
    result = _build_carbone_options(mock_config)

    assert result['language'] == 'en'
    assert result['format'] == 'pdf'
    assert result['margins']['top'] == 20
    assert result['margins']['left'] == 15


def test_format_role():
    """Test role formatting."""
    assert _format_role('hub_operator') == 'Hub Operator'
    assert _format_role('tenant') == 'Tenant'
    assert _format_role('unknown_role') == 'Unknown Role'


def test_extract_contact_email():
    """Test contact email extraction."""
    organizations = [
        {'contact': {'email': 'first@test.com'}},
        {'contact': {'email': 'second@test.com'}}
    ]

    assert _extract_contact_email(organizations) == 'first@test.com'

    # No emails
    assert _extract_contact_email([]) == 'contact@example.com'


def test_build_scenario_comparison_table(mock_normalized_data):
    """Test scenario comparison table building."""
    standalone = mock_normalized_data['financial_data']['scenarios'][0]
    hub = mock_normalized_data['financial_data']['scenarios'][1]
    partnership_terms = mock_normalized_data['partnership_terms']

    result = _build_scenario_comparison_table(standalone, hub, partnership_terms)

    assert 'header' in result
    assert 'rows' in result
    assert len(result['header']) == 4
    assert len(result['rows']) == 4
    assert result['rows'][0][0] == 'Initial Investment'
    assert 'IDR 200,000,000' in result['rows'][0][1]


def test_build_three_year_projection_table(mock_normalized_data):
    """Test three-year projection table building."""
    financial_data = mock_normalized_data['financial_data']

    result = _build_three_year_projection_table(financial_data)

    assert 'header' in result
    assert 'rows' in result
    assert len(result['rows']) == 4  # Year 1, 2, 3, Total


def test_format_benchmark_value():
    """Test benchmark value formatting."""
    # IDR currency
    benchmark = {'value': 30000000, 'unit': 'idr'}
    assert _format_benchmark_value(benchmark) == 'IDR 30,000,000'

    # Percentage
    benchmark = {'value': 0.12, 'unit': 'pct'}
    assert _format_benchmark_value(benchmark) == '12.0%'

    # Other
    benchmark = {'value': 100, 'unit': 'sqm'}
    assert _format_benchmark_value(benchmark) == '100'