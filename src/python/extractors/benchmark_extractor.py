"""
Benchmark Extractor module for extracting pricing benchmarks and market metrics.

This module uses pattern matching and regex to extract financial benchmarks,
pricing ranges, market growth rates, and operational metrics from search result snippets.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from ..config import ConfigLoader

config = ConfigLoader()


def extract_pricing_benchmarks(search_results: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float, str, float, str]]:
    """
    Extract pricing benchmarks from search results.

    Looks for pricing ranges, average prices, and cost information in search snippets.

    Args:
        search_results: List of parsed search result dictionaries

    Returns:
        Dictionary mapping benchmark names to tuples of (min, max, currency, confidence, source)
    """
    benchmarks = {}

    # Common pricing patterns
    pricing_patterns = [
        # Range patterns: "IDR 15.8M to 47.4M", "$100-500", "€50,000 - €100,000"
        r'([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMB]?)\s*(?:to|-|–|—)\s*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMB]?)',
        # Single values: "average $250", "costs IDR 30M"
        r'(?:average|avg|costs?|price|fee|charge)\s*([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMB]?)',
        # Range with currency at end: "15.8M to 47.4M IDR"
        r'(\d+(?:,\d{3})*(?:\.\d+)?)([KMB]?)\s*(?:to|-|–|—)\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMB]?)\s*([A-Z]{3})'
    ]

    for result in search_results:
        snippet = result.get('snippet', '').lower()
        confidence = result.get('confidence', 0.5)
        source = result.get('url', '')

        for pattern in pricing_patterns:
            matches = re.findall(pattern, snippet, re.IGNORECASE)
            for match in matches:
                try:
                    # Parse different pattern formats
                    if len(match) == 6:  # Range with currency
                        currency1, val1, mult1, currency2, val2, mult2 = match
                        if currency1 == currency2 or not currency2:
                            currency = currency1
                            min_val = _parse_numeric_value(val1, mult1)
                            max_val = _parse_numeric_value(val2, mult2)
                        else:
                            continue  # Different currencies, skip
                    elif len(match) == 3:  # Single value
                        currency, val, mult = match
                        min_val = max_val = _parse_numeric_value(val, mult)
                    elif len(match) == 5:  # Range with currency at end
                        val1, mult1, val2, mult2, currency = match
                        min_val = _parse_numeric_value(val1, mult1)
                        max_val = _parse_numeric_value(val2, mult2)
                    else:
                        continue

                    # Determine benchmark type from context
                    benchmark_key = _classify_pricing_benchmark(snippet)

                    if benchmark_key and min_val > 0 and max_val > 0:
                        # Update or create benchmark
                        if benchmark_key not in benchmarks or confidence > benchmarks[benchmark_key][3]:
                            benchmarks[benchmark_key] = (min_val, max_val, currency.upper(), confidence, source)

                except (ValueError, IndexError):
                    continue

    return benchmarks


def extract_market_metrics(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract market metrics like growth rates, market size, etc.

    Args:
        search_results: List of parsed search result dictionaries

    Returns:
        Dictionary of market metrics with values, units, confidence, and sources
    """
    metrics = {}

    # Growth rate patterns: "15% growth", "grew by 25%", "CAGR of 12%"
    growth_patterns = [
        r'(\d+(?:\.\d+)?)%\s*(?:growth|increase|cagr|annual growth)',
        r'grew\s+by\s+(\d+(?:\.\d+)?)%',
        r'(?:growth|increase|cagr)\s+(?:rate\s+)?(?:of\s+)?(\d+(?:\.\d+)?)%'
    ]

    # Market size patterns: "market size $5B", "worth €2.3 billion"
    market_size_patterns = [
        r'market\s+size\s+([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMBT]?)',
        r'worth\s+([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMBT]?)',
        r'valued\s+at\s+([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)([KMBT]?)'
    ]

    for result in search_results:
        snippet = result.get('snippet', '').lower()
        confidence = result.get('confidence', 0.5)
        source = result.get('url', '')

        # Extract growth rates
        for pattern in growth_patterns:
            matches = re.findall(pattern, snippet)
            for match in matches:
                try:
                    rate = float(match)
                    if 0 < rate < 100:  # Reasonable growth rate
                        key = 'market_growth_rate'
                        if key not in metrics or confidence > metrics[key].get('confidence', 0):
                            metrics[key] = {
                                'value': rate / 100,  # Convert to decimal
                                'unit': 'decimal',
                                'confidence': confidence,
                                'source': source
                            }
                except ValueError:
                    continue

        # Extract market size
        for pattern in market_size_patterns:
            matches = re.findall(pattern, snippet, re.IGNORECASE)
            for match in matches:
                try:
                    currency, val, mult = match
                    value = _parse_numeric_value(val, mult)
                    if value > 0:
                        key = 'market_size'
                        if key not in metrics or confidence > metrics[key].get('confidence', 0):
                            metrics[key] = {
                                'value': value,
                                'unit': currency.upper(),
                                'confidence': confidence,
                                'source': source
                            }
                except (ValueError, IndexError):
                    continue

    return metrics


def _parse_numeric_value(value_str: str, multiplier: str) -> float:
    """
    Parse numeric value with multiplier (K, M, B, T).

    Args:
        value_str: String representation of number
        multiplier: K (thousand), M (million), B (billion), T (trillion)

    Returns:
        Parsed float value
    """
    try:
        value = float(value_str.replace(',', ''))
        mult_map = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}
        if multiplier.upper() in mult_map:
            value *= mult_map[multiplier.upper()]
        return value
    except ValueError:
        return 0.0


def _classify_pricing_benchmark(snippet: str) -> Optional[str]:
    """
    Classify the type of pricing benchmark from snippet context.

    Args:
        snippet: Lowercase search snippet

    Returns:
        Benchmark key or None
    """
    # Hair transplant specific
    if 'hair transplant' in snippet or 'hair restoration' in snippet:
        return 'hair_transplant_price'

    # General medical aesthetics
    if 'medical aesthetics' in snippet or 'cosmetic' in snippet:
        return 'medical_aesthetics_price'

    # Clinic costs
    if 'clinic' in snippet and ('cost' in snippet or 'price' in snippet):
        return 'clinic_setup_cost'

    # Default
    if 'price' in snippet or 'cost' in snippet:
        return 'general_service_price'

    return None