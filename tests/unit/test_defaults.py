from src.python.config.defaults import DEFAULTS


class TestDefaults:
    def test_defaults_is_dict(self):
        assert isinstance(DEFAULTS, dict)

    def test_required_keys_present(self):
        required_keys = [
            'research_cache_ttl_days',
            'carbone_api_key',
            'output_dir'
        ]
        for key in required_keys:
            assert key in DEFAULTS

    def test_research_cache_ttl_days(self):
        assert DEFAULTS['research_cache_ttl_days'] == 30
        assert isinstance(DEFAULTS['research_cache_ttl_days'], int)

    def test_carbone_api_key(self):
        assert DEFAULTS['carbone_api_key'] == ''
        assert isinstance(DEFAULTS['carbone_api_key'], str)

    def test_output_directory(self):
        assert DEFAULTS['output_dir'] == './outputs'
        assert isinstance(DEFAULTS['output_dir'], str)

    def test_other_defaults(self):
        # Test some other defaults
        assert DEFAULTS['financial_discount_rate'] == 0.10
        assert DEFAULTS['financial_capex_amortization_months'] == 48
        assert DEFAULTS['log_level'] == 'INFO'
        assert DEFAULTS['research_max_queries_per_gap'] == 3
        assert DEFAULTS['extraction_confidence_threshold'] == 0.75