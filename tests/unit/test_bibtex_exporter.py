"""
Unit tests for bibtex_exporter.py
"""

import os
import tempfile
import pytest
from unittest.mock import Mock
from src.python.formatters.bibtex_exporter import (
    generate_bibtex,
    _create_bibtex_entry,
    _extract_year,
    _format_benchmark_note,
)


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'output_dir': 'outputs'
    }.get(key, default)
    return config


@pytest.fixture
def mock_normalized_data_with_benchmarks():
    """Mock normalized data with market benchmarks."""
    return {
        'research_data': {
            'market_benchmarks': [
                {
                    'category': 'hair_transplant_pricing',
                    'value': 30000000,
                    'unit': 'idr',
                    'source_citation': 'Medical Aesthetics Market Report 2025',
                    'research_date': '2025-01-15',
                    'confidence': 0.85
                },
                {
                    'category': 'market_growth_rate',
                    'value': 0.12,
                    'unit': 'pct',
                    'source_citation': 'Healthcare Industry Analysis',
                    'research_date': '2024-11-01',
                    'confidence': 0.92
                }
            ]
        }
    }


@pytest.fixture
def mock_normalized_data_empty_benchmarks():
    """Mock normalized data with empty benchmarks."""
    return {
        'research_data': {
            'market_benchmarks': []
        }
    }


@pytest.fixture
def mock_normalized_data_no_research():
    """Mock normalized data without research_data."""
    return {}


def test_generate_bibtex_success(mock_normalized_data_with_benchmarks, mock_config):
    """Test successful BibTeX generation with benchmarks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        file_path = generate_bibtex(mock_normalized_data_with_benchmarks, mock_config)

        assert os.path.exists(file_path)
        assert file_path.endswith('references.bib')

        # Verify BibTeX content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '@misc{benchmark1_hairtransplantpricing,' in content
        assert 'title={Medical Aesthetics Market Report 2025}' in content
        assert 'year={2025}' in content
        assert '@misc{benchmark2_marketgrowthrate,' in content
        assert 'title={Healthcare Industry Analysis}' in content
        assert 'year={2024}' in content


def test_generate_bibtex_empty_benchmarks(mock_normalized_data_empty_benchmarks, mock_config):
    """Test BibTeX generation with empty benchmarks creates comment."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        file_path = generate_bibtex(mock_normalized_data_empty_benchmarks, mock_config)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "% No market benchmarks available" in content
        assert "@misc" not in content


def test_generate_bibtex_missing_research_data(mock_normalized_data_no_research, mock_config):
    """Test BibTeX generation with missing research data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        file_path = generate_bibtex(mock_normalized_data_no_research, mock_config)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "% No market benchmarks available" in content


def test_generate_bibtex_file_error(mock_normalized_data_with_benchmarks, mock_config):
    """Test BibTeX generation handles file write errors."""
    mock_config.get.side_effect = lambda key, default=None: {
        'output_dir': '/invalid/path'
    }.get(key, default)

    with pytest.raises(OSError, match="Failed to generate BibTeX"):
        generate_bibtex(mock_normalized_data_with_benchmarks, mock_config)


def test_create_bibtex_entry():
    """Test BibTeX entry creation."""
    benchmark = {
        'category': 'test_category',
        'value': 100,
        'unit': 'idr',
        'source_citation': 'Test Source',
        'research_date': '2025-06-15',
        'confidence': 0.8
    }

    entry = _create_bibtex_entry(benchmark, 1)

    assert entry.startswith('@misc{benchmark1_testcategory,')
    assert 'title={Test Source}' in entry
    assert 'year={2025}' in entry
    assert 'note={Category: Test Category; Value: 100; Unit: idr; Confidence: 0.80}' in entry
    assert entry.endswith('}')


def test_create_bibtex_entry_missing_fields():
    """Test BibTeX entry creation with missing fields."""
    benchmark = {
        'category': 'minimal',
        'source_citation': 'Minimal Source'
    }

    entry = _create_bibtex_entry(benchmark, 2)

    assert '@misc{benchmark2_minimal,' in entry
    assert 'title={Minimal Source}' in entry
    assert 'year={2025}' in entry  # Default year
    assert 'note={Category: Minimal; Confidence: 0.00}' in entry


def test_extract_year():
    """Test year extraction from date strings."""
    assert _extract_year('2025-11-28') == '2025'
    assert _extract_year('2024-01-01T10:00:00Z') == '2024'
    assert _extract_year('2023') == '2023'
    assert _extract_year('') == '2025'  # Default
    assert _extract_year('invalid') == '2025'  # Default


def test_extract_year_edge_cases():
    """Test year extraction edge cases."""
    assert _extract_year('99-12-31') == '99'  # Two-digit year
    assert _extract_year('abcd-ef-gh') == '2025'  # Invalid, returns default
    assert _extract_year(None) == '2025'  # None input


def test_format_benchmark_note():
    """Test benchmark note formatting."""
    benchmark = {
        'category': 'test_category',
        'value': 100,
        'unit': 'idr',
        'confidence': 0.85
    }

    note = _format_benchmark_note(benchmark)
    assert note == "Category: Test Category; Value: 100; Unit: idr; Confidence: 0.85"


def test_format_benchmark_note_missing_fields():
    """Test benchmark note formatting with missing fields."""
    benchmark = {
        'category': 'minimal'
    }

    note = _format_benchmark_note(benchmark)
    assert note == "Category: Minimal; Confidence: 0.00"


def test_format_benchmark_note_edge_cases():
    """Test benchmark note formatting edge cases."""
    # Empty value
    benchmark = {
        'category': 'test',
        'value': '',
        'unit': 'pct',
        'confidence': 0.5
    }
    note = _format_benchmark_note(benchmark)
    assert "Value: " not in note
    assert "Unit: pct" in note

    # Zero confidence
    benchmark['confidence'] = 0
    note = _format_benchmark_note(benchmark)
    assert "Confidence: 0.00" in note

    # No unit
    benchmark['unit'] = ''
    note = _format_benchmark_note(benchmark)
    assert "Unit: " not in note