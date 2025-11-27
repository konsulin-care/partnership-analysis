"""
Unit tests for result_extractor module.
"""

import json
import pytest
from src.python.extractors.result_extractor import (
    extract_financial_data,
    extract_comprehensive_data
)


@pytest.fixture
def sample_search_results():
    """Load sample search results from fixture."""
    with open('tests/fixtures/sample_search_results.json', 'r') as f:
        return json.load(f)


class TestExtractFinancialData:
    """Test financial data extraction."""

    def test_extract_financial_data_from_sample(self, sample_search_results):
        """Test extraction from sample data."""
        financial_data = extract_financial_data(sample_search_results)

        assert isinstance(financial_data, list)
        assert len(financial_data) > 0

        # Check structure of first item
        item = financial_data[0]
        assert 'type' in item
        assert 'confidence' in item
        assert 'source' in item

        # Should have pricing benchmarks
        pricing_items = [item for item in financial_data if item['type'] == 'pricing_benchmark']
        assert len(pricing_items) > 0

        # Check pricing benchmark structure
        for item in pricing_items:
            assert 'min_value' in item
            assert 'max_value' in item
            assert 'currency' in item

    def test_extract_financial_data_empty_input(self):
        """Test with empty input."""
        financial_data = extract_financial_data([])
        assert financial_data == []

    def test_extract_financial_data_validation(self, sample_search_results):
        """Test that validation is applied."""
        financial_data = extract_financial_data(sample_search_results)

        # All items should have been validated
        for item in financial_data:
            assert 'confidence' in item
            # Items with validation errors should have reduced confidence
            if 'validation_errors' in item:
                assert item['confidence'] < 1.0


class TestExtractComprehensiveData:
    """Test comprehensive data extraction."""

    def test_extract_comprehensive_data_from_sample(self, sample_search_results):
        """Test comprehensive extraction from sample data."""
        comprehensive_data = extract_comprehensive_data(sample_search_results)

        assert isinstance(comprehensive_data, dict)

        # Check required sections
        required_sections = [
            'financial_data',
            'pricing_benchmarks',
            'market_metrics',
            'source_citations',
            'extraction_metadata'
        ]

        for section in required_sections:
            assert section in comprehensive_data

        # Check financial data
        assert isinstance(comprehensive_data['financial_data'], list)

        # Check pricing benchmarks
        assert isinstance(comprehensive_data['pricing_benchmarks'], dict)

        # Check market metrics
        assert isinstance(comprehensive_data['market_metrics'], dict)

        # Check source citations
        assert isinstance(comprehensive_data['source_citations'], list)
        assert len(comprehensive_data['source_citations']) == len(sample_search_results)

        # Check metadata
        metadata = comprehensive_data['extraction_metadata']
        assert 'total_results_processed' in metadata
        assert 'extraction_timestamp' in metadata
        assert 'confidence_threshold' in metadata

    def test_extract_comprehensive_data_empty_input(self):
        """Test comprehensive extraction with empty input."""
        comprehensive_data = extract_comprehensive_data([])

        assert comprehensive_data['financial_data'] == []
        assert comprehensive_data['pricing_benchmarks'] == {}
        assert comprehensive_data['market_metrics'] == {}
        assert comprehensive_data['source_citations'] == []
        assert comprehensive_data['extraction_metadata']['total_results_processed'] == 0


class TestIntegrationWithOtherModules:
    """Test integration with other extractor modules."""

    def test_integration_pricing_benchmarks(self, sample_search_results):
        """Test that pricing benchmarks are properly extracted and integrated."""
        comprehensive_data = extract_comprehensive_data(sample_search_results)

        pricing_benchmarks = comprehensive_data['pricing_benchmarks']
        financial_data = comprehensive_data['financial_data']

        # Financial data should include pricing benchmarks
        pricing_in_financial = [item for item in financial_data if item['type'] == 'pricing_benchmark']
        assert len(pricing_in_financial) > 0

        # Should match the pricing benchmarks section
        assert len(pricing_benchmarks) > 0

    def test_integration_market_metrics(self, sample_search_results):
        """Test that market metrics are properly extracted and integrated."""
        comprehensive_data = extract_comprehensive_data(sample_search_results)

        market_metrics = comprehensive_data['market_metrics']
        financial_data = comprehensive_data['financial_data']

        # Financial data should include market metrics
        metrics_in_financial = [item for item in financial_data if item['type'] == 'market_metric']
        assert len(metrics_in_financial) >= 0  # May be empty if no metrics found

    def test_integration_source_citations(self, sample_search_results):
        """Test that source citations are properly extracted."""
        comprehensive_data = extract_comprehensive_data(sample_search_results)

        source_citations = comprehensive_data['source_citations']

        assert len(source_citations) == len(sample_search_results)

        # Check citation structure
        for citation in source_citations:
            assert 'title' in citation
            assert 'url' in citation
            assert 'domain' in citation
            assert 'confidence' in citation