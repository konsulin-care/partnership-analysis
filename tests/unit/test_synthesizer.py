import pytest
from src.python.research.synthesizer import synthesize_market_data


class TestSynthesizer:
    """Test suite for synthesizer functions."""

    def test_synthesize_market_data_empty_findings(self):
        """Test synthesize_market_data with empty findings list."""
        result = synthesize_market_data([])

        expected = {
            'overall': {
                'total_findings': 0,
                'unique_sources': 0,
                'average_confidence': 0.0
            }
        }
        assert result == expected

    def test_synthesize_market_data_numeric_values(self):
        """Test synthesize_market_data with numeric benchmark values."""
        findings = [
            {
                'benchmark_type': 'pricing',
                'value': 100.0,
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'pricing',
                'value': 200.0,
                'confidence': 0.9,
                'source': 'source2.com'
            },
            {
                'benchmark_type': 'pricing',
                'value': 150.0,
                'confidence': 0.7,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'market_growth',
                'value': 0.05,
                'confidence': 0.6,
                'source': 'source3.com'
            }
        ]

        result = synthesize_market_data(findings)

        # Check pricing benchmark
        assert 'pricing' in result
        pricing = result['pricing']
        assert pricing['average'] == 150.0  # (100 + 200 + 150) / 3
        assert pricing['min'] == 100.0
        assert pricing['max'] == 200.0
        assert pricing['count'] == 3
        assert pricing['confidence'] == pytest.approx(0.8)  # (0.8 + 0.9 + 0.7) / 3
        assert set(pricing['sources']) == {'source1.com', 'source2.com'}

        # Check market_growth benchmark
        assert 'market_growth' in result
        growth = result['market_growth']
        assert growth['average'] == 0.05
        assert growth['min'] == 0.05
        assert growth['max'] == 0.05
        assert growth['count'] == 1
        assert growth['confidence'] == 0.6
        assert growth['sources'] == ['source3.com']

        # Check overall
        overall = result['overall']
        assert overall['total_findings'] == 4
        assert overall['unique_sources'] == 3
        assert overall['average_confidence'] == pytest.approx(0.75)  # (0.8 + 0.9 + 0.7 + 0.6) / 4

    def test_synthesize_market_data_non_numeric_values(self):
        """Test synthesize_market_data with non-numeric benchmark values."""
        findings = [
            {
                'benchmark_type': 'competitors',
                'value': 'Company A',
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'competitors',
                'value': 'Company B',
                'confidence': 0.9,
                'source': 'source2.com'
            },
            {
                'benchmark_type': 'competitors',
                'value': 'Company A',  # duplicate
                'confidence': 0.7,
                'source': 'source1.com'
            }
        ]

        result = synthesize_market_data(findings)

        assert 'competitors' in result
        competitors = result['competitors']
        assert set(competitors['values']) == {'Company A', 'Company B'}
        assert competitors['count'] == 2  # unique values
        assert competitors['confidence'] == pytest.approx(0.8)  # (0.8 + 0.9 + 0.7) / 3
        assert set(competitors['sources']) == {'source1.com', 'source2.com'}

    def test_synthesize_market_data_mixed_numeric_non_numeric(self):
        """Test synthesize_market_data with mixed numeric and non-numeric values."""
        findings = [
            {
                'benchmark_type': 'mixed_type',
                'value': 100,
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'mixed_type',
                'value': 'text value',
                'confidence': 0.9,
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        # Should treat as non-numeric since not all are numeric
        assert 'mixed_type' in result
        mixed = result['mixed_type']
        assert set(mixed['values']) == {'100', 'text value'}  # converted to strings
        assert mixed['count'] == 2
        assert mixed['confidence'] == pytest.approx(0.85)  # (0.8 + 0.9) / 2
        assert set(mixed['sources']) == {'source1.com', 'source2.com'}

    def test_synthesize_market_data_none_values(self):
        """Test synthesize_market_data with None values."""
        findings = [
            {
                'benchmark_type': 'test_type',
                'value': None,
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'test_type',
                'value': 100,
                'confidence': 0.9,
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        # None values should be excluded from calculations
        assert 'test_type' in result
        test_type = result['test_type']
        assert test_type['average'] == 100.0
        assert test_type['count'] == 1  # Only the valid value
        assert test_type['confidence'] == pytest.approx(0.85)  # (0.8 + 0.9) / 2

    def test_synthesize_market_data_missing_fields(self):
        """Test synthesize_market_data with missing fields."""
        findings = [
            {
                'value': 100,
                'confidence': 0.8,
                'source': 'source1.com'
                # missing benchmark_type
            },
            {
                'benchmark_type': 'test_type',
                'value': 200,
                # missing confidence
                'source': 'source2.com'
            },
            {
                'benchmark_type': 'test_type',
                'value': 300,
                'confidence': 0.9
                # missing source
            }
        ]

        result = synthesize_market_data(findings)

        # First finding goes to 'general' benchmark_type
        assert 'general' in result
        general = result['general']
        assert general['average'] == 100.0
        assert general['count'] == 1
        assert general['confidence'] == 0.8
        assert general['sources'] == ['source1.com']

        # Second finding has default confidence of 0.5
        # Third finding has empty source
        assert 'test_type' in result
        test_type = result['test_type']
        assert test_type['average'] == 250.0  # (200 + 300) / 2
        assert test_type['count'] == 2
        assert test_type['confidence'] == pytest.approx(0.7)  # (0.5 + 0.9) / 2
        assert set(test_type['sources']) == {'source2.com', ''}  # includes empty string

    def test_synthesize_market_data_zero_confidence(self):
        """Test synthesize_market_data with zero confidence values."""
        findings = [
            {
                'benchmark_type': 'test_type',
                'value': 100,
                'confidence': 0.0,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'test_type',
                'value': 200,
                'confidence': 0.0,
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        assert 'test_type' in result
        test_type = result['test_type']
        assert test_type['average'] == 150.0
        assert test_type['confidence'] == 0.0

        overall = result['overall']
        assert overall['average_confidence'] == 0.0

    def test_synthesize_market_data_single_finding(self):
        """Test synthesize_market_data with single finding."""
        findings = [
            {
                'benchmark_type': 'single',
                'value': 42,
                'confidence': 1.0,
                'source': 'unique.com'
            }
        ]

        result = synthesize_market_data(findings)

        assert 'single' in result
        single = result['single']
        assert single['average'] == 42.0
        assert single['min'] == 42.0
        assert single['max'] == 42.0
        assert single['count'] == 1
        assert single['confidence'] == 1.0
        assert single['sources'] == ['unique.com']

        overall = result['overall']
        assert overall['total_findings'] == 1
        assert overall['unique_sources'] == 1
        assert overall['average_confidence'] == 1.0

    def test_synthesize_market_data_duplicate_sources(self):
        """Test synthesize_market_data with duplicate sources."""
        findings = [
            {
                'benchmark_type': 'test',
                'value': 100,
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'test',
                'value': 200,
                'confidence': 0.9,
                'source': 'source1.com'  # duplicate
            },
            {
                'benchmark_type': 'other',
                'value': 300,
                'confidence': 0.7,
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        # Check deduplication of sources
        assert result['test']['sources'] == ['source1.com']
        assert result['other']['sources'] == ['source2.com']

        overall = result['overall']
        assert overall['unique_sources'] == 2  # source1 and source2

    def test_synthesize_market_data_large_numbers(self):
        """Test synthesize_market_data with large numbers."""
        findings = [
            {
                'benchmark_type': 'large_nums',
                'value': 1000000,
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'large_nums',
                'value': 2000000,
                'confidence': 0.9,
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        large_nums = result['large_nums']
        assert large_nums['average'] == 1500000.0
        assert large_nums['min'] == 1000000
        assert large_nums['max'] == 2000000

    def test_synthesize_market_data_float_precision(self):
        """Test synthesize_market_data with float precision."""
        findings = [
            {
                'benchmark_type': 'precision',
                'value': 0.123456789,
                'confidence': 0.8,
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'precision',
                'value': 0.987654321,
                'confidence': 0.9,
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        precision = result['precision']
        expected_avg = (0.123456789 + 0.987654321) / 2
        assert precision['average'] == pytest.approx(expected_avg)

    def test_synthesize_market_data_many_benchmark_types(self):
        """Test synthesize_market_data with many different benchmark types."""
        findings = []
        for i in range(10):
            findings.append({
                'benchmark_type': f'type_{i}',
                'value': i * 10,
                'confidence': 0.5 + i * 0.05,
                'source': f'source{i}.com'
            })

        result = synthesize_market_data(findings)

        # Should have 10 different benchmark types plus overall
        assert len(result) == 11  # 10 types + overall
        assert 'overall' in result

        for i in range(10):
            type_key = f'type_{i}'
            assert type_key in result
            benchmark = result[type_key]
            assert benchmark['average'] == i * 10
            assert benchmark['count'] == 1
            assert benchmark['sources'] == [f'source{i}.com']

    def test_synthesize_market_data_confidence_bounds(self):
        """Test synthesize_market_data with confidence values at bounds."""
        findings = [
            {
                'benchmark_type': 'bounds',
                'value': 100,
                'confidence': 0.0,  # minimum
                'source': 'source1.com'
            },
            {
                'benchmark_type': 'bounds',
                'value': 200,
                'confidence': 1.0,  # maximum
                'source': 'source2.com'
            }
        ]

        result = synthesize_market_data(findings)

        bounds = result['bounds']
        assert bounds['confidence'] == 0.5  # (0.0 + 1.0) / 2

        overall = result['overall']
        assert overall['average_confidence'] == 0.5