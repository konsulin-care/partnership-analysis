from src.python.config.defaults import DEFAULTS


class TestDefaults:
    def test_defaults_is_dict(self):
        assert isinstance(DEFAULTS, dict)

    def test_required_keys_present(self):
        required_keys = [
            'RESEARCH_CACHE_TTL_DAYS',
            'CARBONE_API_KEY',
            'OUTPUT_DIR'
        ]
        for key in required_keys:
            assert key in DEFAULTS

    def test_research_cache_ttl_days(self):
        assert DEFAULTS['RESEARCH_CACHE_TTL_DAYS'] == 30
        assert isinstance(DEFAULTS['RESEARCH_CACHE_TTL_DAYS'], int)

    def test_carbone_api_key(self):
        assert DEFAULTS['CARBONE_API_KEY'] == ''
        assert isinstance(DEFAULTS['CARBONE_API_KEY'], str)

    def test_output_directory(self):
        assert DEFAULTS['OUTPUT_DIR'] == './outputs'
        assert isinstance(DEFAULTS['OUTPUT_DIR'], str)

    def test_other_defaults(self):
        # Test some other defaults
        assert DEFAULTS['FINANCIAL_DISCOUNT_RATE'] == 0.10
        assert DEFAULTS['FINANCIAL_CAPEX_AMORTIZATION_MONTHS'] == 48
        assert DEFAULTS['LOG_LEVEL'] == 'INFO'
        assert DEFAULTS['RESEARCH_MAX_QUERIES_PER_GAP'] == 3
        assert DEFAULTS['EXTRACTION_CONFIDENCE_THRESHOLD'] == 0.75