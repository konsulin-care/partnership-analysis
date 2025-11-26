from src.python.config.defaults import DEFAULTS


class TestDefaults:
    def test_defaults_is_dict(self):
        assert isinstance(DEFAULTS, dict)

    def test_required_keys_present(self):
        required_keys = [
            'research_cache_ttl_days',
            'web_search_timeout',
            'carbone_api_key',
            'output_directory'
        ]
        for key in required_keys:
            assert key in DEFAULTS

    def test_research_cache_ttl_days(self):
        assert DEFAULTS['research_cache_ttl_days'] == 30
        assert isinstance(DEFAULTS['research_cache_ttl_days'], int)

    def test_web_search_timeout(self):
        assert DEFAULTS['web_search_timeout'] == 30
        assert isinstance(DEFAULTS['web_search_timeout'], int)

    def test_carbone_api_key(self):
        assert DEFAULTS['carbone_api_key'] == ''
        assert isinstance(DEFAULTS['carbone_api_key'], str)

    def test_output_directory(self):
        assert DEFAULTS['output_directory'] == 'outputs'
        assert isinstance(DEFAULTS['output_directory'], str)

    def test_other_defaults(self):
        # Test some other defaults
        assert DEFAULTS['discount_rate'] == 0.10
        assert DEFAULTS['capex_amortization_years'] == 5
        assert DEFAULTS['log_level'] == 'INFO'
        assert DEFAULTS['research_query_limit'] == 3
        assert DEFAULTS['extraction_confidence_threshold'] == 0.70