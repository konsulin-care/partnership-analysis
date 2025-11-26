import pytest
from src.python.config.validators import validate_config


class TestValidateConfig:
    def test_valid_config(self):
        # Test with all required keys and valid types
        config = {
            'research_cache_ttl_days': 30,
            'web_search_timeout': 30,
            'carbone_api_key': 'test_key',
            'output_directory': 'outputs'
        }
        assert validate_config(config) is True

    def test_missing_required_key(self):
        # Test missing required key
        config = {
            'web_search_timeout': 30,
            'carbone_api_key': 'test_key',
            'output_directory': 'outputs'
            # missing research_cache_ttl_days
        }
        with pytest.raises(ValueError, match="Missing required config key: research_cache_ttl_days"):
            validate_config(config)

    def test_invalid_type(self):
        # Test invalid type for research_cache_ttl_days
        config = {
            'research_cache_ttl_days': 'not_an_int',
            'web_search_timeout': 30,
            'carbone_api_key': 'test_key',
            'output_directory': 'outputs'
        }
        with pytest.raises(ValueError, match="research_cache_ttl_days must be an integer"):
            validate_config(config)

    def test_missing_multiple_keys(self):
        # Test missing multiple keys
        config = {
            'research_cache_ttl_days': 30
            # missing others
        }
        with pytest.raises(ValueError, match="Missing required config key: web_search_timeout"):
            validate_config(config)