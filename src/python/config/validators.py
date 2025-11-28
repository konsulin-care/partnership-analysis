def validate_config(config):
    """
    Validate the configuration dictionary.

    Args:
        config (dict): Configuration dictionary to validate.

    Raises:
        ValueError: If required keys are missing or invalid.
    """
    required_keys = [
        'research_cache_ttl_days',
        'web_search_timeout',
        'carbone_api_key',
        'output_dir'
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    # Validate types if needed
    def is_int_like(value):
        return isinstance(value, int) or (isinstance(value, str) and value.isdigit())

    if not is_int_like(config.get('research_cache_ttl_days')):
        raise ValueError("research_cache_ttl_days must be an integer")
    # Validate deep research parameters
    if not is_int_like(config.get('deep_research_max_iterations')) or int(config.get('deep_research_max_iterations')) < 1:
        raise ValueError("deep_research_max_iterations must be an integer >= 1")
    if not isinstance(config.get('deep_research_model_search'), str) or not config.get('deep_research_model_search'):
        raise ValueError("deep_research_model_search must be a non-empty string")
    if not isinstance(config.get('deep_research_model_synthesis'), str) or not config.get('deep_research_model_synthesis'):
        raise ValueError("deep_research_model_synthesis must be a non-empty string")
    if not isinstance(config.get('deep_research_model_questions'), str) or not config.get('deep_research_model_questions'):
        raise ValueError("deep_research_model_questions must be a non-empty string")
    if not is_int_like(config.get('deep_research_iteration_timeout')) or int(config.get('deep_research_iteration_timeout')) < 1:
        raise ValueError("deep_research_iteration_timeout must be an integer >= 1")
    if not is_int_like(config.get('deep_research_cache_ttl_days')) or int(config.get('deep_research_cache_ttl_days')) < 1:
        raise ValueError("deep_research_cache_ttl_days must be an integer >= 1")
    if not is_int_like(config.get('deep_research_gap_threshold')) or int(config.get('deep_research_gap_threshold')) < 1:
        raise ValueError("deep_research_gap_threshold must be an integer >= 1")
    # Add more validations as needed
    return True