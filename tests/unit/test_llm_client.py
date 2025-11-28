import pytest
from unittest.mock import patch, MagicMock
from src.python.research.llm_client import LLMClient, LLMClientError
from src.python.config.config_loader import ConfigLoader


class TestLLMClient:
    @patch('src.python.research.llm_client.genai')
    def test_initialization_success(self, mock_genai):
        # Mock config loader
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        # Mock model initialization
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        client = LLMClient(config_loader=mock_config)

        assert 'gemini-2.0-flash' in client.clients
        assert 'gemini-2.5-flash' in client.clients
        mock_genai.configure.assert_called_once_with(api_key='test_api_key')
        assert mock_genai.GenerativeModel.call_count == 2

    @patch('src.python.research.llm_client.genai')
    def test_initialization_missing_api_key(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = ''

        with pytest.raises(LLMClientError, match="Google GenAI API key not configured"):
            LLMClient(config_loader=mock_config)

    @patch('src.python.research.llm_client.genai')
    def test_execute_prompt_success(self, mock_genai):
        # Setup
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        # Execute
        result = client.execute_prompt('gemini-2.5-flash', 'Test prompt')

        # Assert
        assert result == "Test response"
        mock_model.generate_content.assert_called_once()

    @patch('src.python.research.llm_client.genai')
    def test_execute_prompt_unsupported_model(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'
        mock_genai.GenerativeModel.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        with pytest.raises(LLMClientError, match="Unsupported model"):
            client.execute_prompt('unsupported-model', 'Test prompt')

    @patch('src.python.research.llm_client.genai')
    def test_execute_prompt_generation_error(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        with pytest.raises(LLMClientError, match="Failed to execute prompt"):
            client.execute_prompt('gemini-2.5-flash', 'Test prompt')

    @patch('src.python.research.llm_client.genai')
    def test_adjust_search_terms_success(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Improved query"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        result = client.adjust_search_terms("original query", "context")

        assert result == "Improved query"

    @patch('src.python.research.llm_client.genai')
    def test_adjust_search_terms_error_fallback(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        result = client.adjust_search_terms("original query", "context")

        assert result == "original query"  # Fallback to original

    @patch('src.python.research.llm_client.genai')
    def test_synthesize_findings_success(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Synthesized narrative"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        findings = [{"benchmark": "test"}]
        result = client.synthesize_findings(findings)

        assert result == "Synthesized narrative"

    @patch('src.python.research.llm_client.genai')
    def test_synthesize_findings_error_fallback(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        findings = [{"benchmark": "test"}]
        result = client.synthesize_findings(findings)

        assert "Synthesis failed" in result
        assert "Raw findings" in result

    @patch('src.python.research.llm_client.genai')
    @patch('src.python.research.llm_client.json.loads')
    def test_generate_questions_success(self, mock_json_loads, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '["Question 1", "Question 2"]'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        mock_json_loads.return_value = ["Question 1", "Question 2"]

        client = LLMClient(config_loader=mock_config)

        result = client.generate_questions("topic", "context")

        assert result == ["Question 1", "Question 2"]
        mock_json_loads.assert_called_once_with('["Question 1", "Question 2"]')

    @patch('src.python.research.llm_client.genai')
    def test_generate_questions_error_fallback(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.return_value = 'test_api_key'

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        result = client.generate_questions("topic", "context")

        assert result == []