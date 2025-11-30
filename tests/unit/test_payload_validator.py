"""
Unit tests for payload_validator.py
"""

from unittest.mock import Mock
import pytest
from src.python.renderers.payload_validator import PayloadValidator


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'supported_languages': ['en', 'id'],
        'report_language': 'en',
        'pdf_margin_top': 20,
        'pdf_margin_bottom': 20,
        'pdf_margin_left': 15,
        'pdf_margin_right': 15,
        'carbone_template_id': 'partnership_report_v1'
    }.get(key, default)
    return config


@pytest.fixture
def valid_payload():
    """Valid Carbone payload for testing."""
    return {
        'data': {
            'document': {'title': 'Test Report'},
            'executive_summary': {'headline': 'Test summary'},
            'partnership_overview': {'parties': []},
            'financial_analysis': {'sections': []},
            'market_research': {'sections': []},
            'recommendations': {'primary': 'Test recommendation'}
        },
        'template': 'test_template_v1',
        'options': {
            'language': 'en',
            'format': 'pdf',
            'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        }
    }


class TestPayloadValidator:
    """Test cases for PayloadValidator class."""

    def test_init(self, mock_config):
        """Test PayloadValidator initialization."""
        validator = PayloadValidator(mock_config)

        assert validator.config == mock_config
        assert validator.required_payload_keys == {'data', 'template', 'options'}
        assert 'document' in validator.required_data_keys
        assert 'executive_summary' in validator.required_data_keys

    def test_validate_payload_valid(self, mock_config, valid_payload):
        """Test validation of valid payload."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator.validate_payload(valid_payload)

        assert is_valid
        assert errors == []

    def test_validate_payload_invalid_type(self, mock_config):
        """Test validation fails for non-dict payload."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator.validate_payload("not a dict")

        assert not is_valid
        assert "Payload must be a dictionary" in errors[0]

    def test_validate_payload_missing_keys(self, mock_config):
        """Test validation fails for missing required keys."""
        validator = PayloadValidator(mock_config)
        invalid_payload = {'data': {}}

        is_valid, errors = validator.validate_payload(invalid_payload)

        assert not is_valid
        assert any("Missing required payload keys" in error for error in errors)

    def test_validate_data_section_valid(self, mock_config, valid_payload):
        """Test data section validation."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_data_section(valid_payload['data'])

        assert is_valid
        assert errors == []

    def test_validate_data_section_missing_keys(self, mock_config):
        """Test data section validation fails with missing keys."""
        validator = PayloadValidator(mock_config)
        incomplete_data = {'document': {'title': 'Test'}}

        is_valid, errors = validator._validate_data_section(incomplete_data)

        assert not is_valid
        assert any("Missing required data keys" in error for error in errors)

    def test_validate_data_section_invalid_type(self, mock_config):
        """Test data section validation fails for non-dict."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_data_section("not a dict")

        assert not is_valid
        assert "Data section must be a dictionary" in errors[0]

    def test_validate_data_section_content_document(self, mock_config):
        """Test document section content validation."""
        validator = PayloadValidator(mock_config)

        # Valid document
        valid_doc = {'title': 'Test Report'}
        is_valid, errors = validator._validate_data_section_content('document', valid_doc)
        assert is_valid

        # Invalid document - no title
        invalid_doc = {'author': 'Test'}
        is_valid, errors = validator._validate_data_section_content('document', invalid_doc)
        assert not is_valid
        assert "must have a title" in errors[0]

        # Invalid type
        is_valid, errors = validator._validate_data_section_content('document', "not a dict")
        assert not is_valid
        assert "must be a dictionary" in errors[0]

    def test_validate_data_section_content_other_sections(self, mock_config):
        """Test other section content validation."""
        validator = PayloadValidator(mock_config)

        sections = ['executive_summary', 'partnership_overview', 'financial_analysis', 'market_research', 'recommendations']

        for section in sections:
            # Valid section
            is_valid, errors = validator._validate_data_section_content(section, {'test': 'data'})
            assert is_valid

            # Invalid type
            is_valid, errors = validator._validate_data_section_content(section, "not a dict")
            assert not is_valid
            assert "must be a dictionary" in errors[0]

    def test_validate_data_section_content_none_value(self, mock_config):
        """Test section content validation with None value."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_data_section_content('document', None)

        assert not is_valid
        assert "cannot be None" in errors[0]

    def test_validate_template_valid(self, mock_config):
        """Test template validation."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_template('valid_template')
        assert is_valid
        assert errors == []

    def test_validate_template_invalid_type(self, mock_config):
        """Test template validation fails for non-string."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_template(123)

        assert not is_valid
        assert "Template must be a string" in errors[0]

    def test_validate_template_empty(self, mock_config):
        """Test template validation fails for empty string."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_template('')

        assert not is_valid
        assert "Template cannot be empty" in errors[0]

    def test_validate_template_too_long(self, mock_config):
        """Test template validation fails for too long string."""
        validator = PayloadValidator(mock_config)
        long_template = 'a' * 101

        is_valid, errors = validator._validate_template(long_template)

        assert not is_valid
        assert "Template identifier too long" in errors[0]

    def test_validate_options_valid(self, mock_config):
        """Test options validation."""
        validator = PayloadValidator(mock_config)
        valid_options = {
            'language': 'en',
            'format': 'pdf',
            'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        }

        is_valid, errors = validator._validate_options(valid_options)

        assert is_valid
        assert errors == []

    def test_validate_options_invalid_type(self, mock_config):
        """Test options validation fails for non-dict."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_options("not a dict")

        assert not is_valid
        assert "Options must be a dictionary" in errors[0]

    def test_validate_options_missing_keys(self, mock_config):
        """Test options validation fails for missing required keys."""
        validator = PayloadValidator(mock_config)
        incomplete_options = {'language': 'en'}

        is_valid, errors = validator._validate_options(incomplete_options)

        assert not is_valid
        assert any("Missing required options" in error for error in errors)

    def test_validate_options_invalid_format(self, mock_config):
        """Test options validation fails for invalid format."""
        validator = PayloadValidator(mock_config)
        invalid_options = {
            'language': 'en',
            'format': 'docx',  # Only pdf supported
            'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        }

        is_valid, errors = validator._validate_options(invalid_options)

        assert not is_valid
        assert "Only 'pdf' format is supported" in errors[0]

    def test_validate_options_unsupported_language(self, mock_config):
        """Test options validation fails for unsupported language."""
        validator = PayloadValidator(mock_config)
        invalid_options = {
            'language': 'fr',  # Not in supported languages
            'format': 'pdf',
            'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        }

        is_valid, errors = validator._validate_options(invalid_options)

        assert not is_valid
        assert "Unsupported language" in errors[0]

    def test_validate_margins_valid(self, mock_config):
        """Test margins validation."""
        validator = PayloadValidator(mock_config)
        valid_margins = {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}

        is_valid, errors = validator._validate_margins(valid_margins)

        assert is_valid
        assert errors == []

    def test_validate_margins_invalid_type(self, mock_config):
        """Test margins validation fails for non-dict."""
        validator = PayloadValidator(mock_config)

        is_valid, errors = validator._validate_margins("not a dict")

        assert not is_valid
        assert "Margins must be a dictionary" in errors[0]

    def test_validate_margins_missing_keys(self, mock_config):
        """Test margins validation fails for missing keys."""
        validator = PayloadValidator(mock_config)
        incomplete_margins = {'top': 20, 'left': 15}

        is_valid, errors = validator._validate_margins(incomplete_margins)

        assert not is_valid
        assert any("Missing margin settings" in error for error in errors)

    def test_validate_margins_invalid_values(self, mock_config):
        """Test margins validation fails for invalid values."""
        validator = PayloadValidator(mock_config)

        # Non-numeric value
        invalid_margins = {'top': '20', 'bottom': 20, 'left': 15, 'right': 15}
        is_valid, errors = validator._validate_margins(invalid_margins)
        assert not is_valid
        assert "must be a number" in errors[0]

        # Negative value
        invalid_margins = {'top': -5, 'bottom': 20, 'left': 15, 'right': 15}
        is_valid, errors = validator._validate_margins(invalid_margins)
        assert not is_valid
        assert "cannot be negative" in errors[0]

        # Too large value
        invalid_margins = {'top': 150, 'bottom': 20, 'left': 15, 'right': 15}
        is_valid, errors = validator._validate_margins(invalid_margins)
        assert not is_valid
        assert "too large" in errors[0]

    def test_validate_and_suggest_fixes_valid(self, mock_config, valid_payload):
        """Test validate and suggest fixes for valid payload."""
        validator = PayloadValidator(mock_config)

        is_valid, errors, suggested = validator.validate_and_suggest_fixes(valid_payload)

        assert is_valid
        assert errors == []
        assert suggested == valid_payload

    def test_validate_and_suggest_fixes_missing_sections(self, mock_config):
        """Test validate and suggest fixes adds missing sections."""
        validator = PayloadValidator(mock_config)
        incomplete_payload = {}  # No template, data, or options

        is_valid, errors, suggested = validator.validate_and_suggest_fixes(incomplete_payload)

        assert not is_valid
        assert 'data' in suggested
        assert 'template' in suggested
        assert 'options' in suggested
        assert suggested['template'] == 'partnership_report_v1'
        assert suggested['options']['language'] == 'en'
        assert suggested['options']['format'] == 'pdf'

    def test_validate_and_suggest_fixes_invalid_input(self, mock_config):
        """Test validate and suggest fixes handles invalid input."""
        validator = PayloadValidator(mock_config)

        is_valid, errors, suggested = validator.validate_and_suggest_fixes("not a dict")

        assert not is_valid
        assert isinstance(suggested, dict)
        assert 'data' in suggested
        assert 'template' in suggested
        assert 'options' in suggested