"""
Unit tests for validator module.
"""

import json
import pytest
from src.python.extractors.validator import (
    validate_extracted_values,
    validate_extraction_results,
    filter_valid_results,
    _validate_pricing_benchmark,
    _validate_market_metric,
    _validate_general_values
)


@pytest.fixture
def sample_extracted_data():
    """Sample extracted data for testing."""
    return [
        {
            'type': 'pricing_benchmark',
            'metric': 'hair_transplant_price',
            'min_value': 15800000,
            'max_value': 47400000,
            'currency': 'IDR',
            'confidence': 0.85,
            'source': 'https://example.com'
        },
        {
            'type': 'market_metric',
            'metric': 'market_growth_rate',
            'value': 0.15,
            'unit': 'decimal',
            'confidence': 0.80,
            'source': 'https://market.com'
        },
        {
            'type': 'pricing_benchmark',
            'metric': 'invalid_price',
            'min_value': -100,  # Invalid negative value
            'max_value': 100,
            'currency': 'IDR',
            'confidence': 0.50,
            'source': 'https://example.com'
        }
    ]


class TestValidateExtractedValues:
    """Test value validation."""

    def test_validate_valid_pricing_benchmark(self):
        """Test validation of valid pricing benchmark."""
        data = {
            'type': 'pricing_benchmark',
            'min_value': 1000000,
            'max_value': 5000000,
            'currency': 'IDR',
            'confidence': 0.85,
            'source': 'https://example.com'
        }
        is_valid, errors = validate_extracted_values(data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_invalid_pricing_benchmark(self):
        """Test validation of invalid pricing benchmark."""
        data = {
            'type': 'pricing_benchmark',
            'min_value': -100,  # Invalid
            'max_value': 100,
            'currency': 'INVALID',  # Invalid
            'confidence': 0.50,
            'source': 'https://example.com'
        }
        is_valid, errors = validate_extracted_values(data)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_valid_market_metric(self):
        """Test validation of valid market metric."""
        data = {
            'type': 'market_metric',
            'metric': 'market_growth_rate',
            'value': 0.15,
            'unit': 'decimal',
            'confidence': 0.80,
            'source': 'https://example.com'
        }
        is_valid, errors = validate_extracted_values(data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_invalid_market_metric(self):
        """Test validation of invalid market metric."""
        data = {
            'type': 'market_metric',
            'metric': 'market_growth_rate',
            'value': 1.5,  # Invalid: > 1
            'unit': 'decimal',
            'confidence': 0.80,
            'source': 'https://example.com'
        }
        is_valid, errors = validate_extracted_values(data)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_low_confidence(self):
        """Test validation with low confidence score."""
        data = {
            'type': 'pricing_benchmark',
            'min_value': 1000000,
            'max_value': 5000000,
            'currency': 'IDR',
            'confidence': 0.50,  # Below threshold
            'source': 'https://example.com'
        }
        is_valid, errors = validate_extracted_values(data)
        assert not is_valid  # Should fail due to low confidence

    def test_validate_missing_fields(self):
        """Test validation with missing required fields."""
        data = {
            'type': 'pricing_benchmark',
            'min_value': 1000000,
            'max_value': 5000000,
            'currency': 'IDR'
            # Missing confidence and source
        }
        is_valid, errors = validate_extracted_values(data)
        assert not is_valid
        assert 'below threshold' in str(errors)  # Confidence defaults to 0, below threshold


class TestValidatePricingBenchmark:
    """Test pricing benchmark validation."""

    def test_valid_pricing_benchmark(self):
        """Test valid pricing benchmark."""
        data = {
            'min_value': 1000000,
            'max_value': 5000000,
            'currency': 'IDR'
        }
        errors = _validate_pricing_benchmark(data)
        assert len(errors) == 0

    def test_invalid_negative_values(self):
        """Test negative values."""
        data = {
            'min_value': -100,
            'max_value': 100,
            'currency': 'IDR'
        }
        errors = _validate_pricing_benchmark(data)
        assert len(errors) > 0
        assert 'positive' in str(errors)

    def test_invalid_range(self):
        """Test min > max."""
        data = {
            'min_value': 5000000,
            'max_value': 1000000,
            'currency': 'IDR'
        }
        errors = _validate_pricing_benchmark(data)
        assert len(errors) > 0
        assert 'exceed' in str(errors)

    def test_invalid_currency(self):
        """Test invalid currency format."""
        data = {
            'min_value': 1000000,
            'max_value': 5000000,
            'currency': 'invalid'
        }
        errors = _validate_pricing_benchmark(data)
        assert len(errors) > 0
        assert 'currency' in str(errors)


class TestValidateMarketMetric:
    """Test market metric validation."""

    def test_valid_growth_rate(self):
        """Test valid growth rate."""
        data = {
            'metric': 'market_growth_rate',
            'value': 0.15
        }
        errors = _validate_market_metric(data)
        assert len(errors) == 0

    def test_invalid_growth_rate(self):
        """Test invalid growth rate."""
        data = {
            'metric': 'market_growth_rate',
            'value': 1.5  # Too high
        }
        errors = _validate_market_metric(data)
        assert len(errors) > 0


class TestValidateExtractionResults:
    """Test extraction results validation."""

    def test_validate_extraction_results(self, sample_extracted_data):
        """Test validation of extraction results."""
        summary = validate_extraction_results(sample_extracted_data)

        assert 'total_results' in summary
        assert 'valid_results' in summary
        assert 'invalid_results' in summary
        assert 'validation_rate' in summary
        assert summary['total_results'] == len(sample_extracted_data)
        assert summary['validation_rate'] <= 1.0


class TestFilterValidResults:
    """Test filtering valid results."""

    def test_filter_valid_results(self, sample_extracted_data):
        """Test filtering to valid results only."""
        valid_results = filter_valid_results(sample_extracted_data, strict=True)
        assert len(valid_results) < len(sample_extracted_data)

        # Non-strict should include more
        non_strict_results = filter_valid_results(sample_extracted_data, strict=False)
        assert len(non_strict_results) >= len(valid_results)