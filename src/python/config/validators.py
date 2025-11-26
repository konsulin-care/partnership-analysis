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
        'output_directory'
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    # Validate types if needed
    if not isinstance(config.get('research_cache_ttl_days'), int):
        raise ValueError("research_cache_ttl_days must be an integer")
    # Add more validations as needed
    return True