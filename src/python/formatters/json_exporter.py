"""
JSON Exporter Module

Serializes normalized partnership analysis data to JSON format for API consumption
and data interchange.
"""

import json
import os
from typing import Dict, Any, List
from ..config.config_loader import ConfigLoader


def serialize_to_json(
    normalized_data: Dict[str, Any],
    config: ConfigLoader
) -> str:
    """
    Serialize normalized data to JSON file.

    Exports the complete normalized partnership analysis data structure to a JSON file
    for API consumption, data integration, and archival purposes.

    Args:
        normalized_data: Normalized partnership analysis data
        config: Configuration loader instance

    Returns:
        Path to the exported JSON file

    Raises:
        ValueError: If normalized data is invalid
        OSError: If file cannot be written
    """
    try:
        if not normalized_data:
            raise ValueError("Normalized data cannot be empty")

        # Validate basic structure
        required_keys = ['metadata', 'organizations', 'partnership_terms', 'financial_data']
        missing_keys = [key for key in required_keys if key not in normalized_data]
        if missing_keys:
            raise ValueError(f"Missing required keys in normalized data: {missing_keys}")

        # Prepare output directory
        output_dir = config.get('output_dir', 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        # Export to JSON
        json_path = os.path.join(output_dir, 'normalized_data.json')

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, indent=2, ensure_ascii=False)

        return json_path

    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to encode normalized data as JSON: {e}") from e
    except OSError as e:
        raise OSError(f"Failed to write JSON file: {e}") from e