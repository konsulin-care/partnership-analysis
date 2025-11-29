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
    # Validate formatter output paths
    output_patterns = [
        'output_csv_file_pattern',
        'output_json_file_pattern',
        'output_bibtex_file_pattern',
        'output_pdf_file_pattern',
        'output_txt_file_pattern'
    ]
    for pattern in output_patterns:
        if not isinstance(config.get(pattern), str) or not config.get(pattern):
            raise ValueError(f"{pattern} must be a non-empty string")
    # Validate formatting options
    if not isinstance(config.get('csv_delimiter'), str) or len(config.get('csv_delimiter')) != 1:
        raise ValueError("csv_delimiter must be a single character string")
    if not is_int_like(config.get('json_indent')) or int(config.get('json_indent')) < 0:
        raise ValueError("json_indent must be an integer >= 0")
    if not isinstance(config.get('bibtex_style'), str) or not config.get('bibtex_style'):
        raise ValueError("bibtex_style must be a non-empty string")
    # Validate Carbone configuration
    if not isinstance(config.get('carbone_template_id'), str):
        raise ValueError("carbone_template_id must be a string")
    if not isinstance(config.get('carbone_api_version'), str) or not config.get('carbone_api_version'):
        raise ValueError("carbone_api_version must be a non-empty string")
    if not is_int_like(config.get('carbone_render_timeout')) or int(config.get('carbone_render_timeout')) <= 0:
        raise ValueError("carbone_render_timeout must be an integer > 0")
    # Validate TXT intermediary preferences
    if not isinstance(config.get('txt_section_separator'), str):
        raise ValueError("txt_section_separator must be a string")
    if not isinstance(config.get('txt_include_timestamps'), bool):
        raise ValueError("txt_include_timestamps must be a boolean")
    # Add more validations as needed
    return True