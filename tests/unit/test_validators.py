import pytest
from src.python.config.validators import validate_config


class TestValidateConfig:
    def test_valid_config(self):
        # Test with a valid configuration
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 3,
            'deep_research_model_search': 'gemini-2.0-flash',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 300,
            'deep_research_cache_ttl_days': 7,
            'deep_research_gap_threshold': 3
        }
        assert validate_config(config) is True

    def test_missing_required_key(self):
        config = {
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs'
        }
        with pytest.raises(ValueError, match="Missing required config key: research_cache_ttl_days"):
            validate_config(config)

    def test_invalid_research_cache_ttl_days_type(self):
        config = {
            'research_cache_ttl_days': 'not_an_int',
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 3,
            'deep_research_model_search': 'gemini-2.0-flash',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 300,
            'deep_research_cache_ttl_days': 7,
            'deep_research_gap_threshold': 3
        }
        with pytest.raises(ValueError, match="research_cache_ttl_days must be an integer"):
            validate_config(config)

    def test_invalid_deep_research_max_iterations(self):
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 0,
            'deep_research_model_search': 'gemini-2.0-flash',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 300,
            'deep_research_cache_ttl_days': 7,
            'deep_research_gap_threshold': 3
        }
        with pytest.raises(ValueError, match="deep_research_max_iterations must be an integer >= 1"):
            validate_config(config)

    def test_invalid_deep_research_model_search(self):
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 3,
            'deep_research_model_search': '',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 300,
            'deep_research_cache_ttl_days': 7,
            'deep_research_gap_threshold': 3
        }
        with pytest.raises(ValueError, match="deep_research_model_search must be a non-empty string"):
            validate_config(config)

    def test_invalid_deep_research_iteration_timeout(self):
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 3,
            'deep_research_model_search': 'gemini-2.0-flash',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 0,
            'deep_research_cache_ttl_days': 7,
            'deep_research_gap_threshold': 3
        }
        with pytest.raises(ValueError, match="deep_research_iteration_timeout must be an integer >= 1"):
            validate_config(config)

    def test_invalid_deep_research_cache_ttl_days(self):
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 3,
            'deep_research_model_search': 'gemini-2.0-flash',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 300,
            'deep_research_cache_ttl_days': -1,
            'deep_research_gap_threshold': 3
        }
        with pytest.raises(ValueError, match="deep_research_cache_ttl_days must be an integer >= 1"):
            validate_config(config)

    def test_invalid_deep_research_gap_threshold(self):
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 10,
            'carbone_api_key': 'test_key',
            'output_dir': './outputs',
            'deep_research_max_iterations': 3,
            'deep_research_model_search': 'gemini-2.0-flash',
            'deep_research_model_synthesis': 'gemini-2.5-flash',
            'deep_research_model_questions': 'gemini-2.5-flash',
            'deep_research_iteration_timeout': 300,
            'deep_research_cache_ttl_days': 7,
            'deep_research_gap_threshold': 'not_an_int'
        }
        with pytest.raises(ValueError, match="deep_research_gap_threshold must be an integer >= 1"):
            validate_config(config)