"""
Unit tests for carbone_renderer.py
"""

import os
import tempfile
from unittest.mock import Mock, patch, mock_open
import pytest
from src.python.renderers.carbone_renderer import CarboneRenderer


@pytest.fixture
def mock_config():
    """Mock ConfigLoader instance."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'carbone_secret_access_token': 'test_secret_token_123',
        'carbone_api_version': 'v3',
        'carbone_template_id': 'test_template_v1',
        'report_language': 'en',
        'pdf_margin_top': 20,
        'pdf_margin_bottom': 20,
        'pdf_margin_left': 15,
        'pdf_margin_right': 15
    }.get(key, default)
    return config


@pytest.fixture
def mock_carbone_sdk():
    """Mock CarboneSDK class."""
    mock_sdk = Mock()
    mock_sdk.return_value = mock_sdk  # Constructor returns instance
    mock_sdk.render.return_value = (b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nendobj\n%%EOF', 'unique_report_123')
    mock_sdk.set_api_version = Mock()
    return mock_sdk


@pytest.fixture
def sample_payload():
    """Sample Carbone payload for testing."""
    return {
        'data': {
            'document': {'title': 'Test Report'},
            'executive_summary': {'headline': 'Test summary'}
        },
        'template': 'test_template_v1',
        'options': {
            'language': 'en',
            'format': 'pdf',
            'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        }
    }


class TestCarboneRenderer:
    """Test cases for CarboneRenderer class."""

    def test_init(self, mock_config):
        """Test CarboneRenderer initialization."""
        renderer = CarboneRenderer(mock_config)
        assert renderer.config == mock_config
        assert renderer.client is None
        assert not renderer._initialized

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_initialize_carbone_client_success(self, mock_sdk_class, mock_config):
        """Test successful Carbone client initialization."""
        mock_client = Mock()
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        client = renderer.initialize_carbone_client()

        assert client == mock_client
        assert renderer.client == mock_client
        assert renderer._initialized
        mock_sdk_class.assert_called_once_with(secret_access_token='test_secret_token_123')
        mock_client.set_api_version.assert_called_once_with('v3')

    @patch('src.python.renderers.carbone_renderer.CarboneSDK', None)
    def test_initialize_carbone_client_no_sdk(self, mock_config):
        """Test initialization fails when Carbone SDK not available."""
        renderer = CarboneRenderer(mock_config)

        with pytest.raises(RuntimeError, match="Carbone SDK is not installed"):
            renderer.initialize_carbone_client()

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_initialize_carbone_client_no_secret_token(self, mock_sdk_class, mock_config):
        """Test initialization fails when secret access token not in config."""
        # Override the side_effect to return None for carbone_secret_access_token
        def side_effect(key, default=None):
            if key == 'carbone_secret_access_token':
                return None
            return default
        mock_config.get.side_effect = side_effect

        renderer = CarboneRenderer(mock_config)

        with pytest.raises(ValueError, match="Carbone secret access token not found in configuration"):
            renderer.initialize_carbone_client()

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_initialize_carbone_client_custom_secret_token(self, mock_sdk_class, mock_config):
        """Test initialization with custom secret access token."""
        mock_client = Mock()
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        client = renderer.initialize_carbone_client(secret_access_token='custom_token')

        mock_sdk_class.assert_called_once_with(secret_access_token='custom_token')
        mock_client.set_api_version.assert_called_once_with('v3')


    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_initialize_carbone_client_exception(self, mock_sdk_class, mock_config):
        """Test initialization handles SDK exceptions."""
        mock_sdk_class.side_effect = Exception("SDK error")

        renderer = CarboneRenderer(mock_config)

        with pytest.raises(RuntimeError, match="Carbone client initialization failed: SDK error"):
            renderer.initialize_carbone_client()

    def test_prepare_carbone_payload_default_template(self, mock_config):
        """Test payload preparation with default template."""
        renderer = CarboneRenderer(mock_config)
        data = {'test': 'data'}

        payload = renderer.prepare_carbone_payload(data)

        assert payload['data'] == data
        assert payload['template'] == 'test_template_v1'
        assert payload['options']['language'] == 'en'
        assert payload['options']['format'] == 'pdf'
        assert payload['options']['margins']['top'] == 20

    def test_prepare_carbone_payload_custom_template(self, mock_config):
        """Test payload preparation with custom template."""
        renderer = CarboneRenderer(mock_config)
        data = {'test': 'data'}

        payload = renderer.prepare_carbone_payload(data, template_id='custom_template')

        assert payload['template'] == 'custom_template'

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_render_to_pdf_success(self, mock_sdk_class, mock_config, sample_payload):
        """Test successful PDF rendering."""
        mock_client = Mock()
        mock_client.render.return_value = (b'fake_pdf_data', 'unique_report_123')
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        renderer.client = mock_client
        renderer._initialized = True

        result = renderer.render_to_pdf(sample_payload)

        assert result == b'fake_pdf_data'
        mock_client.render.assert_called_once_with('test_template_v1', sample_payload['data'], sample_payload['options'])

    def test_render_to_pdf_not_initialized(self, mock_config, sample_payload):
        """Test rendering fails when client not initialized."""
        renderer = CarboneRenderer(mock_config)

        with pytest.raises(RuntimeError, match="Carbone client initialization failed"):
            renderer.render_to_pdf(sample_payload)

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_render_to_pdf_with_client_param(self, mock_sdk_class, mock_config, sample_payload):
        """Test rendering with client parameter."""
        mock_client = Mock()
        mock_client.render.return_value = (b'pdf_data', 'unique_report_456')

        renderer = CarboneRenderer(mock_config)
        result = renderer.render_to_pdf(sample_payload, client=mock_client)

        assert result == b'pdf_data'
        mock_client.render.assert_called_once_with('test_template_v1', sample_payload['data'], sample_payload['options'])

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_render_to_pdf_exception(self, mock_sdk_class, mock_config, sample_payload):
        """Test rendering handles exceptions."""
        mock_client = Mock()
        mock_client.render.side_effect = Exception("Render failed")
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        renderer.client = mock_client
        renderer._initialized = True

        with pytest.raises(RuntimeError, match="Carbone rendering failed: Render failed"):
            renderer.render_to_pdf(sample_payload)

    def test_save_pdf_success(self, mock_config):
        """Test successful PDF saving."""
        renderer = CarboneRenderer(mock_config)
        pdf_data = b'test pdf content'

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test.pdf')

            result_path = renderer.save_pdf(pdf_data, output_path)

            assert result_path == os.path.abspath(output_path)
            assert os.path.exists(output_path)

            with open(output_path, 'rb') as f:
                assert f.read() == pdf_data

    def test_save_pdf_creates_directory(self, mock_config):
        """Test PDF saving creates output directory."""
        renderer = CarboneRenderer(mock_config)
        pdf_data = b'test pdf content'

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'subdir', 'test.pdf')

            result_path = renderer.save_pdf(pdf_data, output_path)

            assert os.path.exists(output_path)
            assert os.path.exists(os.path.dirname(output_path))

    def test_save_pdf_write_error(self, mock_config):
        """Test PDF saving handles write errors."""
        renderer = CarboneRenderer(mock_config)
        pdf_data = b'test pdf content'

        # Try to write to a directory that doesn't exist and can't be created
        with patch('os.makedirs', side_effect=OSError("Permission denied")):
            with pytest.raises(IOError, match="Failed to save PDF"):
                renderer.save_pdf(pdf_data, '/invalid/path/test.pdf')

    def test_validate_pdf_integrity_valid(self, mock_config):
        """Test PDF integrity validation for valid PDF."""
        renderer = CarboneRenderer(mock_config)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF')
            temp_file_path = temp_file.name

        try:
            is_valid, error_msg = renderer.validate_pdf_integrity(temp_file_path)
            assert is_valid
            assert error_msg == ""
        finally:
            os.unlink(temp_file_path)

    def test_validate_pdf_integrity_file_not_exists(self, mock_config):
        """Test PDF validation when file doesn't exist."""
        renderer = CarboneRenderer(mock_config)

        is_valid, error_msg = renderer.validate_pdf_integrity('/nonexistent/file.pdf')
        assert not is_valid
        assert "does not exist" in error_msg

    def test_validate_pdf_integrity_empty_file(self, mock_config):
        """Test PDF validation for empty file."""
        renderer = CarboneRenderer(mock_config)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            is_valid, error_msg = renderer.validate_pdf_integrity(temp_file_path)
            assert not is_valid
            assert "empty" in error_msg
        finally:
            os.unlink(temp_file_path)

    def test_validate_pdf_integrity_invalid_header(self, mock_config):
        """Test PDF validation for invalid header."""
        renderer = CarboneRenderer(mock_config)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b'Not a PDF file')
            temp_file_path = temp_file.name

        try:
            is_valid, error_msg = renderer.validate_pdf_integrity(temp_file_path)
            assert not is_valid
            assert "Invalid PDF header" in error_msg
        finally:
            os.unlink(temp_file_path)

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_render_and_save_success(self, mock_sdk_class, mock_config):
        """Test successful render and save operation."""
        mock_client = Mock()
        mock_client.render.return_value = (b'%PDF-1.4\nfake content\n%%EOF', 'unique_report_789')
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        data = {'test': 'data'}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'output.pdf')

            result_path = renderer.render_and_save(data, output_path)

            assert result_path == os.path.abspath(output_path)
            assert os.path.exists(output_path)
            mock_client.render.assert_called_once()

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_render_and_save_validation_warning(self, mock_sdk_class, mock_config):
        """Test render and save with PDF validation warning."""
        mock_client = Mock()
        mock_client.render.return_value = (b'invalid pdf content', 'unique_report_999')
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        data = {'test': 'data'}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'output.pdf')

            # Should not raise exception even with invalid PDF
            result_path = renderer.render_and_save(data, output_path)
            assert result_path == os.path.abspath(output_path)

    @patch('src.python.renderers.carbone_renderer.CarboneSDK')
    def test_render_and_save_render_failure(self, mock_sdk_class, mock_config):
        """Test render and save handles render failure."""
        mock_client = Mock()
        mock_client.render.side_effect = Exception("Render failed")
        mock_sdk_class.return_value = mock_client

        renderer = CarboneRenderer(mock_config)
        data = {'test': 'data'}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'output.pdf')

            with pytest.raises(RuntimeError, match="Carbone rendering failed"):
                renderer.render_and_save(data, output_path)