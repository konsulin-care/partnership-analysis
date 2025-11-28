import os
import tempfile
import pytest
from unittest.mock import patch
from src.python.config.config_loader import ConfigLoader


class TestConfigLoader:
    def test_load_from_env(self):
        # Test loading from environment variables
        with patch.dict(os.environ, {'TEST_KEY': 'test_value'}):
            loader = ConfigLoader(env_path='/nonexistent')  # No .env file
            assert loader.get('TEST_KEY') == 'test_value'

    def test_load_from_yaml(self):
        # Test loading from YAML file
        yaml_content = """
        yaml_key: yaml_value
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            loader = ConfigLoader(env_path=None, config_path=f.name)
            assert loader.get('yaml_key') == 'yaml_value'
            os.unlink(f.name)

    def test_default_merging(self):
        # Test that defaults are merged when not in env or yaml
        with patch('os.environ', {}):
            loader = ConfigLoader(env_path='/nonexistent', config_path=None)
            assert loader.get('research_cache_ttl_days') == 30  # from defaults
            assert loader.get('output_dir') == './outputs'

    def test_env_overrides_defaults(self):
        # Test that env overrides defaults
        with patch.dict(os.environ, {'research_cache_ttl_days': '60'}):
            loader = ConfigLoader(env_path=None)
            assert loader.get('research_cache_ttl_days') == '60'  # string from env

    def test_yaml_overrides_env_and_defaults(self):
        # Test that yaml overrides env and defaults
        yaml_content = """
        research_cache_ttl_days: 90
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            with patch.dict(os.environ, {'research_cache_ttl_days': '60'}):
                loader = ConfigLoader(env_path=None, config_path=f.name)
                assert loader.get('research_cache_ttl_days') == 90
            os.unlink(f.name)

    def test_get_method(self):
        with patch('os.environ', {}):
            loader = ConfigLoader(env_path='/nonexistent')
            assert loader.get('nonexistent', 'default') == 'default'
            assert loader.get('research_cache_ttl_days') == 30

    def test_getitem(self):
        with patch('os.environ', {}):
            loader = ConfigLoader(env_path='/nonexistent')
            assert loader['research_cache_ttl_days'] == 30

    def test_contains(self):
        with patch('os.environ', {}):
            loader = ConfigLoader(env_path='/nonexistent')
            assert 'research_cache_ttl_days' in loader
            assert 'nonexistent' not in loader

    def test_deep_research_parameters_loaded(self):
        # Test that deep research parameters are loaded from defaults
        with patch('os.environ', {}):
            loader = ConfigLoader(env_path='/nonexistent')
            assert loader.get('deep_research_max_iterations') == 3
            assert loader.get('deep_research_model_search') == 'gemini-2.0-flash'
            assert loader.get('deep_research_model_synthesis') == 'gemini-2.5-flash'
            assert loader.get('deep_research_model_questions') == 'gemini-2.5-flash'
            assert loader.get('deep_research_iteration_timeout') == 300
            assert loader.get('deep_research_cache_ttl_days') == 7
            assert loader.get('deep_research_gap_threshold') == 3

    def test_deep_research_parameters_from_env(self):
        # Test that deep research parameters can be overridden from env
        env_vars = {
            'deep_research_max_iterations': '5',
            'deep_research_model_search': 'custom-model',
            'deep_research_cache_ttl_days': '10'
        }
        with patch.dict(os.environ, env_vars):
            loader = ConfigLoader(env_path='/nonexistent')
            assert loader.get('deep_research_max_iterations') == '5'  # string from env
            assert loader.get('deep_research_model_search') == 'custom-model'
            assert loader.get('deep_research_cache_ttl_days') == '10'
            # Others should still be defaults
            assert loader.get('deep_research_model_synthesis') == 'gemini-2.5-flash'