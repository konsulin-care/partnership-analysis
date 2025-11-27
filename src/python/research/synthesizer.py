"""
Synthesizer module for aggregating and synthesizing market data from parsed search findings.

This module takes a list of extracted findings from web search results and synthesizes
them into coherent market data dictionaries, aggregating benchmarks, sources, and confidence scores.
"""

from typing import List, Dict, Any
from collections import defaultdict


def synthesize_market_data(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesize market data from a list of parsed search findings.

    Aggregates benchmarks by type, calculates averages, ranges, and confidence scores,
    and collects sources for attribution.

    Args:
        findings: List of dictionaries, each representing an extracted finding with keys:
            - 'benchmark_type': str (e.g., 'pricing', 'market_growth', 'operational_costs')
            - 'value': numeric or str (the extracted benchmark value)
            - 'confidence': float (confidence score, 0.0 to 1.0)
            - 'source': str (source URL or citation)
            - Other optional keys as needed

    Returns:
        Dictionary containing synthesized market data:
        {
            'benchmark_type': {
                'average': float (if numeric),
                'min': float,
                'max': float,
                'count': int,
                'confidence': float (average confidence),
                'sources': List[str] (unique sources)
            },
            'overall': {
                'total_findings': int,
                'unique_sources': int,
                'average_confidence': float
            }
        }
    """
    if not findings:
        return {
            'overall': {
                'total_findings': 0,
                'unique_sources': 0,
                'average_confidence': 0.0
            }
        }

    # Group findings by benchmark_type
    aggregated = defaultdict(lambda: {
        'values': [],
        'confidences': [],
        'sources': []
    })

    all_sources = []

    for finding in findings:
        benchmark_type = finding.get('benchmark_type', 'general')
        value = finding.get('value')
        confidence = finding.get('confidence', 0.5)
        source = finding.get('source', '')

        aggregated[benchmark_type]['values'].append(value)
        aggregated[benchmark_type]['confidences'].append(confidence)
        aggregated[benchmark_type]['sources'].append(source)
        all_sources.append(source)

    # Synthesize each benchmark type
    synthesized = {}
    for b_type, data in aggregated.items():
        values = [v for v in data['values'] if v is not None]
        confidences = data['confidences']
        sources = list(set(data['sources']))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        if values and all(isinstance(v, (int, float)) for v in values):
            # Numeric aggregation
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            synthesized[b_type] = {
                'average': avg_value,
                'min': min_value,
                'max': max_value,
                'count': len(values),
                'confidence': avg_confidence,
                'sources': sources
            }
        else:
            # Non-numeric or mixed: collect unique values
            unique_values = list(set(str(v) for v in values if v is not None))
            synthesized[b_type] = {
                'values': unique_values,
                'count': len(unique_values),
                'confidence': avg_confidence,
                'sources': sources
            }

    # Overall statistics
    overall_confidence = sum(f.get('confidence', 0.5) for f in findings) / len(findings)
    unique_sources = len(set(all_sources))

    synthesized['overall'] = {
        'total_findings': len(findings),
        'unique_sources': unique_sources,
        'average_confidence': overall_confidence
    }

    return synthesized