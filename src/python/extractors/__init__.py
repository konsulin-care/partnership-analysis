"""
Data Extraction Module for parsing web search results and extracting structured entities.

This module provides components for extracting financial benchmarks, pricing ranges,
market growth rates, operational metrics, and source citations from web search results,
with confidence scores and attribution tracking.
"""

from .result_extractor import extract_financial_data
from .benchmark_extractor import extract_pricing_benchmarks, extract_market_metrics
from .citation_extractor import extract_source_citations
from .validators import validate_extracted_values

__all__ = [
    'extract_financial_data',
    'extract_pricing_benchmarks',
    'extract_market_metrics',
    'extract_source_citations',
    'validate_extracted_values'
]