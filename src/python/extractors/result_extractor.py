"""
Result Extractor module for orchestrating extraction from parsed web search results.

This module coordinates the extraction of financial benchmarks, pricing data,
market metrics, and source citations from structured search results.
"""

from typing import List, Dict, Any, Tuple
import re
from ..config import ConfigLoader

config = ConfigLoader()


def extract_financial_data(search_results: List[Dict[str, Any]]) -> List[Dict[str, float]]:
    """
    Extract financial data from search results.

    Processes parsed search results to extract financial benchmarks and metrics
    with confidence scores and source attribution.

    Args:
        search_results: List of parsed search result dictionaries with title, url, snippet, confidence

    Returns:
        List of dictionaries containing extracted financial data with confidence scores
    """
    from .benchmark_extractor import extract_pricing_benchmarks, extract_market_metrics
    from .citation_extractor import extract_source_citations
    from .validator import validate_extracted_values

    extracted_data = []

    # Extract pricing benchmarks
    pricing_data = extract_pricing_benchmarks(search_results)
    if pricing_data:
        for key, (min_val, max_val, currency, confidence, source) in pricing_data.items():
            extracted_data.append({
                'type': 'pricing_benchmark',
                'metric': key,
                'min_value': min_val,
                'max_value': max_val,
                'currency': currency,
                'confidence': confidence,
                'source': source
            })

    # Extract market metrics
    market_data = extract_market_metrics(search_results)
    if market_data:
        for key, value in market_data.items():
            if isinstance(value, dict) and 'value' in value:
                extracted_data.append({
                    'type': 'market_metric',
                    'metric': key,
                    'value': value['value'],
                    'unit': value.get('unit', ''),
                    'confidence': value.get('confidence', 0.5),
                    'source': value.get('source', '')
                })

    # Validate extracted values
    validated_data = []
    for item in extracted_data:
        is_valid, errors = validate_extracted_values(item)
        if is_valid:
            validated_data.append(item)
        else:
            # Flag low confidence but keep for manual review
            item['validation_errors'] = errors
            item['confidence'] *= 0.8
            validated_data.append(item)

    return validated_data


def extract_comprehensive_data(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract comprehensive data including financials, citations, and metadata.

    Args:
        search_results: List of parsed search result dictionaries

    Returns:
        Dictionary containing all extracted data types
    """
    from .benchmark_extractor import extract_pricing_benchmarks, extract_market_metrics
    from .citation_extractor import extract_source_citations

    financial_data = extract_financial_data(search_results)
    pricing_benchmarks = extract_pricing_benchmarks(search_results)
    market_metrics = extract_market_metrics(search_results)
    source_citations = extract_source_citations(search_results)

    return {
        'financial_data': financial_data,
        'pricing_benchmarks': pricing_benchmarks,
        'market_metrics': market_metrics,
        'source_citations': source_citations,
        'extraction_metadata': {
            'total_results_processed': len(search_results),
            'extraction_timestamp': None,  # Could add timestamp
            'confidence_threshold': config.get('extraction_confidence_threshold', 0.75)
        }
    }