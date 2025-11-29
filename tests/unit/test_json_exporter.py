"""
Unit tests for json_exporter.py
"""

import json
import os
import tempfile
import pytest
from unittest.mock import Mock
from src.python.formatters.json_exporter import serialize_to_json


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'output_dir': 'outputs'
    }.get(key, default)
    return config


@pytest.fixture
def mock_normalized_data():
    """Mock normalized data with all required sections."""
    return {
        'metadata': {
            'document_id': 'test_doc_123',
            'generated_at': '2025-11-28T10:00:00Z',
            'schema_version': '1.0'
        },
        'organizations': [
            {
                'name': 'Test Clinic',
                'role': 'tenant',
                'location': {'city': 'Jakarta', 'country': 'Indonesia'}
            }
        ],
        'partnership_terms': {
            'revenue_share_pct': 12.5,
            'capex_investment_idr': 200000000,
            'commitment_years': 3
        },
        'financial_data': {
            'scenarios': [
                {
                    'name': 'standalone',
                    'monthly_revenue_idr': 285000000,
                    'monthly_costs': {'rent_idr': 20000000},
                    'breakeven_months': 24
                }
            ]
        }
    }


@pytest.fixture
def mock_normalized_data_missing_keys():
    """Mock normalized data missing required keys."""
    return {
        'metadata': {},
        # Missing organizations, partnership_terms, financial_data
    }


def test_serialize_to_json_success(mock_normalized_data, mock_config):
    """Test successful JSON serialization with valid data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        file_path = serialize_to_json(mock_normalized_data, mock_config)

        assert os.path.exists(file_path)
        assert file_path.endswith('normalized_data.json')

        # Verify JSON content
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert loaded_data == mock_normalized_data
        assert loaded_data['metadata']['document_id'] == 'test_doc_123'
        assert loaded_data['partnership_terms']['revenue_share_pct'] == 12.5


def test_serialize_to_json_empty_data(mock_config):
    """Test JSON serialization fails with empty data."""
    with pytest.raises(ValueError, match="Normalized data cannot be empty"):
        serialize_to_json({}, mock_config)


def test_serialize_to_json_missing_keys(mock_normalized_data_missing_keys, mock_config):
    """Test JSON serialization fails with missing required keys."""
    with pytest.raises(ValueError, match="Missing required keys in normalized data"):
        serialize_to_json(mock_normalized_data_missing_keys, mock_config)


def test_serialize_to_json_file_error(mock_normalized_data, mock_config):
    """Test JSON serialization handles file write errors."""
    mock_config.get.side_effect = lambda key, default=None: {
        'output_dir': '/invalid/path/that/does/not/exist'
    }.get(key, default)

    with pytest.raises(OSError, match="Failed to write JSON file"):
        serialize_to_json(mock_normalized_data, mock_config)


def test_serialize_to_json_encoding_error(mock_config):
    """Test JSON serialization handles encoding errors."""
    # Create data that might cause encoding issues
    problematic_data = {
        'metadata': {'document_id': 'test', 'generated_at': '2025-01-01T00:00:00Z', 'schema_version': '1.0'},
        'organizations': [],
        'partnership_terms': {'revenue_share_pct': 10, 'capex_investment_idr': 100000000, 'commitment_years': 2},
        'financial_data': {'scenarios': []}
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        # This should work normally
        file_path = serialize_to_json(problematic_data, mock_config)
        assert os.path.exists(file_path)


def test_serialize_to_json_with_unicode(mock_normalized_data, mock_config):
    """Test JSON serialization preserves Unicode characters."""
    mock_normalized_data['organizations'][0]['name'] = 'Test Klinik 中文'

    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get.side_effect = lambda key, default=None: {
            'output_dir': temp_dir
        }.get(key, default)

        file_path = serialize_to_json(mock_normalized_data, mock_config)

        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert loaded_data['organizations'][0]['name'] == 'Test Klinik 中文'