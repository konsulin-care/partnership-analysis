"""
Comprehensive test fixtures for deep research functionality.

This module provides pytest fixtures for testing the DeepResearchEngine,
including sample brand configurations, mock LLM responses, web search results,
expected outputs, and error scenarios.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock


# Sample Brand Configurations
@pytest.fixture
def sample_brand_config_konsulin():
    """Sample brand configuration for Konsulin (IT Service, booking management)."""
    return {
        'BRAND_NAME': 'Konsulin',
        'BRAND_ABOUT': 'Konsulin is a leading IT service provider specializing in booking management systems for healthcare and wellness businesses. We offer comprehensive digital solutions that streamline appointment scheduling, patient management, and operational workflows.',
        'BRAND_ADDRESS': 'Jakarta, Indonesia',
        'BRAND_INDUSTRY': 'IT Service',
        'HUB_LOCATION': 'Jakarta'
    }


@pytest.fixture
def sample_brand_config_medical_aesthetics():
    """Sample brand configuration for medical aesthetics clinic in Jakarta."""
    return {
        'BRAND_NAME': 'Glow Aesthetics Clinic',
        'BRAND_ABOUT': 'Glow Aesthetics Clinic is a premium medical aesthetics center offering advanced cosmetic procedures including laser treatments, injectables, and skin rejuvenation. We serve discerning clients seeking high-quality, medically-supervised beauty treatments.',
        'BRAND_ADDRESS': 'Jakarta, Indonesia',
        'BRAND_INDUSTRY': 'medical aesthetics',
        'HUB_LOCATION': 'Jakarta'
    }


@pytest.fixture
def sample_brand_config_dental():
    """Sample brand configuration for dental clinic in BSD location."""
    return {
        'BRAND_NAME': 'Bright Smile Dental',
        'BRAND_ABOUT': 'Bright Smile Dental provides comprehensive dental care services including general dentistry, cosmetic procedures, orthodontics, and emergency dental care. We focus on patient comfort and use the latest dental technologies.',
        'BRAND_ADDRESS': 'BSD City, Indonesia',
        'BRAND_INDUSTRY': 'dental',
        'HUB_LOCATION': 'Jakarta'
    }


@pytest.fixture
def sample_brand_config_wellness():
    """Sample brand configuration for wellness center in Tangerang."""
    return {
        'BRAND_NAME': 'Harmony Wellness Center',
        'BRAND_ABOUT': 'Harmony Wellness Center offers holistic wellness services including massage therapy, yoga classes, nutritional counseling, and alternative medicine treatments. We create personalized wellness plans for optimal health and well-being.',
        'BRAND_ADDRESS': 'Tangerang, Indonesia',
        'BRAND_INDUSTRY': 'wellness',
        'HUB_LOCATION': 'Jakarta'
    }


# Expected Query Outputs
@pytest.fixture
def expected_queries_konsulin():
    """Expected initial queries for Konsulin brand research."""
    return [
        'Konsulin performance IT Service 2025',
        'Konsulin market share IT Service',
        'Konsulin vs competitors IT Service',
        'IT Service performance Jakarta, Indonesia 2025',
        'IT Service market growth Jakarta',
        'IT Service trends Jakarta, Indonesia vs Jakarta',
        'competitive positioning Konsulin is a leading IT service provider specializing in booking management systems for healthcare and wellness businesses, targeting medical and wellness organizations seeking streamlined digital solutions. IT Service',
        'market analysis Konsulin positioning IT Service',
        'competitors to Konsulin IT Service Jakarta, Indonesia'
    ]


@pytest.fixture
def expected_queries_medical_aesthetics():
    """Expected initial queries for medical aesthetics clinic."""
    return [
        'Glow Aesthetics Clinic performance medical aesthetics 2025',
        'Glow Aesthetics Clinic market share medical aesthetics',
        'Glow Aesthetics Clinic vs competitors medical aesthetics',
        'medical aesthetics performance Jakarta, Indonesia 2025',
        'medical aesthetics market growth Jakarta',
        'medical aesthetics trends Jakarta, Indonesia vs Jakarta',
        'competitive positioning Glow Aesthetics Clinic is a premium medical aesthetics center offering advanced cosmetic procedures, targeting discerning clients seeking high-quality beauty treatments. medical aesthetics',
        'market analysis Glow Aesthetics Clinic positioning medical aesthetics',
        'competitors to Glow Aesthetics Clinic medical aesthetics Jakarta, Indonesia'
    ]


# Mock LLM Responses
@pytest.fixture
def mock_llm_adjust_search_terms():
    """Mock responses for adjust_search_terms method."""
    return {
        'original': 'Konsulin performance IT Service 2025',
        'adjusted': 'Konsulin IT service provider performance metrics 2025 Indonesia healthcare booking systems'
    }


@pytest.fixture
def mock_llm_synthesize_findings():
    """Mock responses for synthesize_findings method."""
    return {
        'findings': [
            {
                'query': 'Konsulin performance IT Service 2025',
                'results': [{'title': 'Konsulin Growth Report', 'snippet': 'Strong performance in 2025'}],
                'synthesis': 'Konsulin shows strong market performance'
            }
        ],
        'synthesis': 'Konsulin demonstrates robust performance in the IT service sector, particularly in healthcare booking management systems. Market analysis indicates strong growth potential and competitive positioning.'
    }


@pytest.fixture
def mock_llm_generate_questions():
    """Mock responses for generate_questions method."""
    return {
        'topic': 'Partnership analysis for Konsulin in IT Service',
        'context': 'Current findings show strong performance',
        'questions': [
            'What are the specific market opportunities for healthcare IT integration?',
            'How does Konsulin compare to competitors in terms of technology adoption?',
            'What are the projected growth rates for booking management systems in Indonesia?'
        ]
    }


@pytest.fixture
def mock_llm_final_synthesis():
    """Mock response for final synthesis execute_prompt."""
    return 'Final comprehensive analysis of Konsulin partnership opportunities reveals strong market positioning, significant growth potential in healthcare IT services, and clear competitive advantages in booking management systems. Recommended for strategic partnership development.'


# Mock Web Search Results
@pytest.fixture
def mock_web_search_results_konsulin():
    """Mock web search results for Konsulin research."""
    return [
        {
            'query': 'Konsulin performance IT Service 2025',
            'results': [
                {
                    'title': 'Konsulin Annual Report 2025',
                    'url': 'https://konsulin.com/report2025',
                    'snippet': 'Konsulin achieved 35% revenue growth in 2025, expanding market share in healthcare IT solutions.',
                    'confidence': 0.95
                },
                {
                    'title': 'IT Service Market Analysis Indonesia',
                    'url': 'https://research.com/it-indonesia',
                    'snippet': 'Healthcare IT services market growing at 28% CAGR, booking management systems showing highest demand.',
                    'confidence': 0.88
                }
            ],
            'synthesis': 'Konsulin demonstrates strong financial performance with significant market share gains in healthcare IT services.'
        },
        {
            'query': 'IT Service performance Jakarta, Indonesia 2025',
            'results': [
                {
                    'title': 'Jakarta IT Services Sector Report',
                    'url': 'https://jakarta-it.com/report',
                    'snippet': 'Jakarta IT services market valued at IDR 50T with 25% annual growth, healthcare segment leading.',
                    'confidence': 0.92
                }
            ],
            'synthesis': 'Jakarta IT services market shows robust growth, particularly in healthcare applications.'
        }
    ]


@pytest.fixture
def mock_web_search_results_medical_aesthetics():
    """Mock web search results for medical aesthetics clinic."""
    return [
        {
            'query': 'Glow Aesthetics Clinic performance medical aesthetics 2025',
            'results': [
                {
                    'title': 'Glow Aesthetics Clinic Review 2025',
                    'url': 'https://glowclinic.com/review',
                    'snippet': 'Glow Aesthetics Clinic reported 40% increase in procedures, premium positioning maintained.',
                    'confidence': 0.90
                }
            ],
            'synthesis': 'Glow Aesthetics Clinic shows strong performance with premium market positioning.'
        },
        {
            'query': 'medical aesthetics performance Jakarta, Indonesia 2025',
            'results': [
                {
                    'title': 'Jakarta Medical Aesthetics Market 2025',
                    'url': 'https://medaesth-jkt.com/market',
                    'snippet': 'Jakarta medical aesthetics market growing 22% annually, premium services demand increasing.',
                    'confidence': 0.85
                }
            ],
            'synthesis': 'Jakarta medical aesthetics market demonstrates strong growth with increasing premium service demand.'
        }
    ]


# Expected Deep Research Results
@pytest.fixture
def expected_deep_research_result_konsulin():
    """Expected complete deep research result for Konsulin."""
    return {
        'brand_hash': 'mock_hash_konsulin',
        'brand_config': {
            'BRAND_NAME': 'Konsulin',
            'BRAND_ABOUT': 'Konsulin is a leading IT service provider...',
            'BRAND_ADDRESS': 'Jakarta, Indonesia',
            'BRAND_INDUSTRY': 'IT Service',
            'HUB_LOCATION': 'Jakarta'
        },
        'iterations': [
            {
                'iteration': 1,
                'adjusted_queries': ['adjusted query 1', 'adjusted query 2'],
                'search_results': [],
                'synthesis': 'Iteration synthesis text',
                'further_questions': ['What are market opportunities?', 'How does it compare?'],
                'timestamp': '2025-11-28T07:51:47.099Z'
            }
        ],
        'all_findings': [],
        'final_synthesis': 'Final comprehensive analysis...',
        'completed_at': '2025-11-28T07:51:47.099Z',
        'total_iterations': 1
    }


@pytest.fixture
def expected_deep_research_result_medical_aesthetics():
    """Expected complete deep research result for medical aesthetics clinic."""
    return {
        'brand_hash': 'mock_hash_glow',
        'brand_config': {
            'BRAND_NAME': 'Glow Aesthetics Clinic',
            'BRAND_ABOUT': 'Glow Aesthetics Clinic is a premium medical aesthetics center...',
            'BRAND_ADDRESS': 'Jakarta, Indonesia',
            'BRAND_INDUSTRY': 'medical aesthetics',
            'HUB_LOCATION': 'Jakarta'
        },
        'iterations': [
            {
                'iteration': 1,
                'adjusted_queries': ['adjusted medical aesthetics query 1'],
                'search_results': [],
                'synthesis': 'Medical aesthetics market analysis synthesis',
                'further_questions': ['What are pricing trends?', 'Competitive landscape?'],
                'timestamp': '2025-11-28T07:51:47.099Z'
            }
        ],
        'all_findings': [],
        'final_synthesis': 'Medical aesthetics partnership analysis reveals strong market potential...',
        'completed_at': '2025-11-28T07:51:47.099Z',
        'total_iterations': 1
    }


# Configuration Variations
@pytest.fixture
def config_max_iterations_1():
    """Configuration with max iterations set to 1."""
    return {
        'max_deep_research_iterations': 1,
        'deep_research_iteration_timeout': 300,
        'min_questions_for_research_gap': 1
    }


@pytest.fixture
def config_max_iterations_3():
    """Configuration with max iterations set to 3."""
    return {
        'max_deep_research_iterations': 3,
        'deep_research_iteration_timeout': 300,
        'min_questions_for_research_gap': 2
    }


@pytest.fixture
def config_short_timeout():
    """Configuration with short iteration timeout."""
    return {
        'max_deep_research_iterations': 3,
        'deep_research_iteration_timeout': 10,
        'min_questions_for_research_gap': 1
    }


# Error Scenarios
@pytest.fixture
def mock_llm_error():
    """Mock LLM client that raises errors."""
    from src.python.research.llm_client import LLMClientError

    mock_client = MagicMock()
    mock_client.adjust_search_terms.side_effect = LLMClientError("LLM adjustment failed")
    mock_client.synthesize_findings.side_effect = LLMClientError("Synthesis failed")
    mock_client.generate_questions.side_effect = LLMClientError("Question generation failed")
    mock_client.execute_prompt.side_effect = LLMClientError("Prompt execution failed")
    return mock_client


@pytest.fixture
def mock_empty_web_search_results():
    """Mock web search that returns empty results."""
    return []


@pytest.fixture
def mock_timeout_web_search():
    """Mock web search that raises timeout errors."""
    import requests

    mock_search = MagicMock()
    mock_search.side_effect = requests.exceptions.Timeout("Search timeout")
    return mock_search


@pytest.fixture
def mock_partial_web_search_results():
    """Mock web search with partial/incomplete results."""
    return [
        {
            'query': 'incomplete query',
            'results': [],
            'synthesis': ''
        }
    ]


# Mock Dependencies
@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock_client = MagicMock()
    mock_client.adjust_search_terms.return_value = "adjusted search query"
    mock_client.synthesize_findings.return_value = "Mock synthesis of findings"
    mock_client.generate_questions.return_value = ["What is the market size?", "Who are competitors?"]
    mock_client.execute_prompt.return_value = "Mock final synthesis response"
    return mock_client


@pytest.fixture
def mock_query_generator():
    """Mock query generator for testing."""
    mock_generator = MagicMock()
    mock_generator.generate_brand_research_queries.return_value = [
        'mock query 1', 'mock query 2', 'mock query 3'
    ]
    return mock_generator


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing."""
    mock_cache = MagicMock()
    mock_cache.get_cached_result.return_value = None  # No cached results by default
    return mock_cache


@pytest.fixture
def mock_config_loader():
    """Mock config loader for testing."""
    mock_config = MagicMock()
    mock_config.get.side_effect = lambda key, default=None: {
        'max_deep_research_iterations': 3,
        'deep_research_iteration_timeout': 300,
        'min_questions_for_research_gap': 1
    }.get(key, default)
    return mock_config


# Integration Test Fixtures
@pytest.fixture
def complete_deep_research_scenario():
    """Complete scenario for integration testing."""
    return {
        'brand_config': {
            'BRAND_NAME': 'Test Clinic',
            'BRAND_ABOUT': 'Test clinic description',
            'BRAND_ADDRESS': 'Test City',
            'BRAND_INDUSTRY': 'healthcare',
            'HUB_LOCATION': 'Test Hub'
        },
        'expected_iterations': 2,
        'expected_final_synthesis': 'Comprehensive analysis completed'
    }