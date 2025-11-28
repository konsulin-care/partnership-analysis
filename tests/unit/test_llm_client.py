import pytest
from unittest.mock import patch, MagicMock
from src.python.research.llm_client import LLMClient, LLMClientError
from src.python.config.config_loader import ConfigLoader


class TestLLMClient:
    @patch('src.python.research.llm_client.genai')
    def test_initialization_success(self, mock_genai):
        # Mock config loader
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        # Mock client initialization
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        client = LLMClient(config_loader=mock_config)

        assert client.rate_limit_delay == 10
        assert client.last_call_time == 0.0
        mock_genai.Client.assert_called_once_with(api_key='test_api_key')

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
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        # Execute
        result = client.execute_prompt('gemini-2.5-flash', 'Test prompt')

        # Assert
        assert result == "Test response"
        mock_client.models.generate_content.assert_called_once()

    @patch('src.python.research.llm_client.genai')
    def test_execute_prompt_unsupported_model(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None
        mock_genai.Client.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        with pytest.raises(LLMClientError, match="Unsupported model"):
            client.execute_prompt('unsupported-model', 'Test prompt')

    @patch('src.python.research.llm_client.genai')
    def test_execute_prompt_generation_error(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        with pytest.raises(LLMClientError, match="Failed to execute prompt"):
            client.execute_prompt('gemini-2.5-flash', 'Test prompt')

    @patch('src.python.research.llm_client.genai')
    def test_adjust_search_terms_success(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Improved query"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        result = client.adjust_search_terms("original query", "context")

        assert result == "Improved query"

    @patch('src.python.research.llm_client.genai')
    def test_adjust_search_terms_error_fallback(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        result = client.adjust_search_terms("original query", "context")

        assert result == "original query"  # Fallback to original

    @patch('src.python.research.llm_client.genai')
    def test_synthesize_findings_success(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Synthesized narrative"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        findings = [{"benchmark": "test"}]
        result = client.synthesize_findings(findings)

        assert result == "Synthesized narrative"

    @patch('src.python.research.llm_client.genai')
    def test_synthesize_findings_error_fallback(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        findings = [{"benchmark": "test"}]
        result = client.synthesize_findings(findings)

        assert "Synthesis failed" in result
        assert "Raw findings" in result

    @patch('src.python.research.llm_client.genai')
    @patch('src.python.research.llm_client.json.loads')
    def test_generate_questions_success(self, mock_json_loads, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '["Question 1", "Question 2"]'
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        mock_json_loads.return_value = ["Question 1", "Question 2"]

        client = LLMClient(config_loader=mock_config)

        result = client.generate_questions("topic", "context")

        assert result == ["Question 1", "Question 2"]
        mock_json_loads.assert_called_once_with('["Question 1", "Question 2"]')

    @patch('src.python.research.llm_client.genai')
    def test_generate_questions_error_fallback(self, mock_genai):
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 10 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        client = LLMClient(config_loader=mock_config)

        result = client.generate_questions("topic", "context")

        assert result == []

    @patch('src.python.research.llm_client.time')
    @patch('src.python.research.llm_client.genai')
    def test_rate_limiting_enforces_delay(self, mock_genai, mock_time):
        # Setup
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 5 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        # Mock time: first call at 0, sleep, then last_call_time=0, second call at 2, sleep again
        mock_time.time.side_effect = [0, 0, 2, 2]
        mock_time.sleep = MagicMock()

        client = LLMClient(config_loader=mock_config)

        # First call: time_since=0 <5, sleep(5)
        client.execute_prompt('gemini-2.5-flash', 'Test prompt 1')
        mock_time.sleep.assert_called_with(5)

        # Second call: time_since=2-0=2 <5, sleep(3)
        mock_time.sleep.reset_mock()
        client.execute_prompt('gemini-2.5-flash', 'Test prompt 2')
        mock_time.sleep.assert_called_with(3)

    @patch('src.python.research.llm_client.time')
    @patch('src.python.research.llm_client.genai')
    def test_rate_limiting_no_delay_when_enough_time_passed(self, mock_genai, mock_time):
        # Setup
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 5 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        # Mock time: first call at 0, last_call_time=0, second call at 6 (>5), no sleep
        mock_time.time.side_effect = [0, 0, 6, 6]
        mock_time.sleep = MagicMock()

        client = LLMClient(config_loader=mock_config)

        # First call
        client.execute_prompt('gemini-2.5-flash', 'Test prompt 1')
        mock_time.sleep.assert_called_with(5)

        # Second call: time_since=6-0=6 >=5, no sleep
        mock_time.sleep.reset_mock()
        client.execute_prompt('gemini-2.5-flash', 'Test prompt 2')
        mock_time.sleep.assert_not_called()

    @patch('src.python.research.llm_client.genai')
    def test_configuration_loading_default_delay(self, mock_genai):
        # Mock config loader to return default for delay (simulating key not set)
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda key, default=None: default if key == 'llm_rate_limit_delay_seconds' else 'test_api_key' if key == 'google_genai_api_key' else None

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        client = LLMClient(config_loader=mock_config)

        # Should default to 10
        assert client.rate_limit_delay == 10

    @patch('src.python.research.llm_client.logger')
    @patch('src.python.research.llm_client.time')
    @patch('src.python.research.llm_client.genai')
    def test_rate_limiting_logs_action(self, mock_genai, mock_time, mock_logger):
        # Setup
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get.side_effect = lambda *args: 'test_api_key' if args[0] == 'google_genai_api_key' else 5 if args[0] == 'llm_rate_limit_delay_seconds' else None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types.GenerateContentConfig.return_value = MagicMock()

        # Mock time: call at 0, last=0, sleep 5
        mock_time.time.side_effect = [0, 0]
        mock_time.sleep = MagicMock()

        client = LLMClient(config_loader=mock_config)

        # Execute
        client.execute_prompt('gemini-2.5-flash', 'Test prompt')

        # Check logging
        mock_logger.info.assert_any_call("Rate limiting: sleeping for 5.00 seconds before API call")