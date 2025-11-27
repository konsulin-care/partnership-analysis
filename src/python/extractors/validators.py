"""
Validator module for validating extracted values and data quality.

This module provides validation functions for extracted financial data,
ensuring data quality, reasonableness, and compliance with expected ranges.
"""

from typing import Dict, Any, Tuple, List
import re
from ..config import ConfigLoader

config = ConfigLoader()


def validate_extracted_values(values: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate extracted values for reasonableness and data quality.

    Args:
        values: Dictionary of extracted values to validate

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Validate based on value type
    value_type = values.get('type', '')

    if value_type == 'pricing_benchmark':
        errors.extend(_validate_pricing_benchmark(values))
    elif value_type == 'market_metric':
        errors.extend(_validate_market_metric(values))
    else:
        # General validation
        errors.extend(_validate_general_values(values))

    # Check confidence score
    confidence = values.get('confidence', 0)
    min_confidence = float(config.get('extraction_confidence_threshold', 0.75))
    if confidence < min_confidence:
        errors.append(f"Confidence score {confidence:.2f} below threshold {min_confidence}")

    return len(errors) == 0, errors


def _validate_pricing_benchmark(values: Dict[str, Any]) -> List[str]:
    """Validate pricing benchmark data."""
    errors = []

    min_val = values.get('min_value', 0)
    max_val = values.get('max_value', 0)
    currency = values.get('currency', '')

    # Check value ranges
    if min_val <= 0:
        errors.append("Minimum price must be positive")
    if max_val <= 0:
        errors.append("Maximum price must be positive")
    if min_val > max_val:
        errors.append("Minimum price cannot exceed maximum price")

    # Check for reasonable ranges (not too extreme)
    if currency == 'IDR':
        if max_val > 500000000:  # 500M IDR is very high for services
            errors.append("Maximum price seems unreasonably high for IDR currency")
        if min_val < 100000:  # 100K IDR is very low
            errors.append("Minimum price seems unreasonably low for IDR currency")
    elif currency in ['USD', 'EUR', 'SGD']:
        if max_val > 100000:  # 100K USD is very high for services
            errors.append("Maximum price seems unreasonably high")
        if min_val < 10:  # 10 USD is very low
            errors.append("Minimum price seems unreasonably low")

    # Check currency format
    if not re.match(r'^[A-Z]{3}$', currency):
        errors.append(f"Invalid currency format: {currency}")

    return errors


def _validate_market_metric(values: Dict[str, Any]) -> List[str]:
    """Validate market metric data."""
    errors = []

    metric = values.get('metric', '')
    value = values.get('value', 0)
    unit = values.get('unit', '')

    if metric == 'market_growth_rate':
        if not (0 < value < 1):  # Should be between 0 and 1 (decimal)
            errors.append("Growth rate should be between 0 and 1 (as decimal)")
        if value > 0.5:  # 50% growth is extremely high
            errors.append("Growth rate seems unreasonably high (>50%)")
    elif metric == 'market_size':
        if value <= 0:
            errors.append("Market size must be positive")
        # Could add currency-specific validation here

    return errors


def _validate_general_values(values: Dict[str, Any]) -> List[str]:
    """General validation for any extracted values."""
    errors = []

    # Check for required fields
    required_fields = ['confidence']
    for field in required_fields:
        if field not in values:
            errors.append(f"Missing required field: {field}")

    # Validate confidence is a number between 0 and 1
    confidence = values.get('confidence')
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        errors.append("Confidence must be a number between 0 and 1")

    # Check source URL if present
    source = values.get('source', '')
    if source and not source.startswith(('http://', 'https://')):
        errors.append("Source URL must be a valid HTTP/HTTPS URL")

    return errors


def validate_extraction_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a complete set of extraction results.

    Args:
        results: List of extraction result dictionaries

    Returns:
        Validation summary with counts and error details
    """
    total_results = len(results)
    valid_results = 0
    invalid_results = 0
    all_errors = []

    for result in results:
        is_valid, errors = validate_extracted_values(result)
        if is_valid:
            valid_results += 1
        else:
            invalid_results += 1
            all_errors.extend(errors)

    # Group errors by type
    error_counts = {}
    for error in all_errors:
        error_type = error.split(':')[0] if ':' in error else error
        error_counts[error_type] = error_counts.get(error_type, 0) + 1

    return {
        'total_results': total_results,
        'valid_results': valid_results,
        'invalid_results': invalid_results,
        'validation_rate': valid_results / total_results if total_results > 0 else 0,
        'error_summary': error_counts,
        'all_errors': all_errors[:10]  # Limit to first 10 errors
    }


def filter_valid_results(results: List[Dict[str, Any]], strict: bool = False) -> List[Dict[str, Any]]:
    """
    Filter results to only include valid ones.

    Args:
        results: List of extraction results
        strict: If True, only include results with no validation errors

    Returns:
        Filtered list of valid results
    """
    valid_results = []

    for result in results:
        is_valid, errors = validate_extracted_values(result)
        if strict and is_valid:
            valid_results.append(result)
        elif not strict:
            # Non-strict: include all results regardless of validation
            valid_results.append(result)

    return valid_results