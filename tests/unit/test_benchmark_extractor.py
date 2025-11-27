"""
Unit tests for benchmark_extractor module.
"""

import json
import pytest
from src.python.extractors.benchmark_extractor import (
    extract_pricing_benchmarks,
    extract_market_metrics,
    _parse_numeric_value,
    _classify_pricing_benchmark
)


@pytest.fixture
def sample_search_results():
    """Load sample search results from fixture."""
    with open('tests/fixtures/sample_search_results.json', 'r') as f:
        return json.load(f)


class TestExtractPricingBenchmarks:
    """Test pricing benchmark extraction."""

    def test_extract_pricing_benchmarks_from_sample(self, sample_search_results):
        """Test extraction from sample data."""
        benchmarks = extract_pricing_benchmarks(sample_search_results)

        assert isinstance(benchmarks, dict)
        assert len(benchmarks) > 0

        # Check for expected benchmarks
        assert 'hair_transplant_price' in benchmarks

        # Verify benchmark structure
        benchmark = benchmarks['hair_transplant_price']
        assert len(benchmark) == 5  # min, max, currency, confidence, source
        min_val, max_val, currency, confidence, source = benchmark

        assert min_val > 0
        assert max_val >= min_val
        assert currency == 'IDR'
        assert 0 <= confidence <= 1
        assert source.startswith('http')

    def test_extract_pricing_benchmarks_empty_input(self):
        """Test with empty input."""
        benchmarks = extract_pricing_benchmarks([])
        assert benchmarks == {}

    def test_extract_pricing_benchmarks_no_matches(self):
        """Test with results that have no pricing info."""
        results = [{
            'title': ['Test Title'],
            'url': ['https://example.com'],
            'snippet': 'This is just some text with no pricing information.',
            'confidence': 0.5
        }]
        benchmarks = extract_pricing_benchmarks(results)
        assert benchmarks == {}


class TestExtractMarketMetrics:
    """Test market metrics extraction."""

    def test_extract_market_metrics_from_sample(self, sample_search_results):
        """Test market metrics extraction from sample data."""
        metrics = extract_market_metrics(sample_search_results)

        assert isinstance(metrics, dict)

        # Check for growth rate
        if 'market_growth_rate' in metrics:
            growth = metrics['market_growth_rate']
            assert 'value' in growth
            assert 'unit' in growth
            assert 'confidence' in growth
            assert 'source' in growth
            assert 0 < growth['value'] < 1  # Should be decimal

    def test_extract_market_metrics_empty_input(self):
        """Test with empty input."""
        metrics = extract_market_metrics([])
        assert metrics == {}


class TestParseNumericValue:
    """Test numeric value parsing."""

    def test_parse_simple_number(self):
        """Test parsing simple numbers."""
        assert _parse_numeric_value('100', '') == 100.0
        assert _parse_numeric_value('1,500', '') == 1500.0
        assert _parse_numeric_value('2.5', '') == 2.5

    def test_parse_with_multipliers(self):
        """Test parsing with K, M, B multipliers."""
        assert _parse_numeric_value('1.5', 'K') == 1500.0
        assert _parse_numeric_value('2', 'M') == 2000000.0
        assert _parse_numeric_value('1.2', 'B') == 1200000000.0
        assert _parse_numeric_value('3', 'T') == 3000000000000.0

    def test_parse_invalid_input(self):
        """Test parsing invalid input."""
        assert _parse_numeric_value('invalid', '') == 0.0
        assert _parse_numeric_value('', 'M') == 0.0


class TestClassifyPricingBenchmark:
    """Test pricing benchmark classification."""

    def test_classify_hair_transplant(self):
        """Test hair transplant classification."""
        snippet = "hair transplant procedures cost idr 30m"
        assert _classify_pricing_benchmark(snippet) == 'hair_transplant_price'

    def test_classify_medical_aesthetics(self):
        """Test medical aesthetics classification."""
        snippet = "medical aesthetics services are expensive"
        assert _classify_pricing_benchmark(snippet) == 'medical_aesthetics_price'

    def test_classify_clinic_cost(self):
        """Test clinic cost classification."""
        snippet = "clinic setup costs approximately 500m"
        assert _classify_pricing_benchmark(snippet) == 'clinic_setup_cost'

    def test_classify_general_price(self):
        """Test general price classification."""
        snippet = "the service costs 100 dollars"
        assert _classify_pricing_benchmark(snippet) == 'general_service_price'

    def test_classify_no_match(self):
        """Test no classification match."""
        snippet = "this text has no pricing information"
        assert _classify_pricing_benchmark(snippet) is None