"""
Schema validation utilities for partnership analysis entities.

This module provides the SchemaValidator class for validating data against JSON schemas
defined in the base_schemas module. It supports collecting all validation errors and
strict mode validation that raises exceptions on failure.
"""

import jsonschema
from typing import Dict, Any, Tuple, List


class SchemaValidator:
    """
    Validator for JSON schema validation of partnership analysis entities.
    
    Supports validation against base schemas with error collection and strict mode.
    """

    def validate_entity_against_schema(
        self,
        entity: Dict[str, Any],
        schema: Dict[str, Any],
        strict_mode: bool = False,
        schema_version: str = "v1"
    ) -> Tuple[bool, List[str]]:
        """
        Validate an entity against a JSON schema.
        
        Args:
            entity: The data dictionary to validate
            schema: The JSON schema dictionary to validate against
            strict_mode: If True, raise ValidationError on validation failure instead of returning errors
            schema_version: Schema version string for future versioning support (currently unused)
        
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
            If valid, returns (True, [])
            If invalid and strict_mode=False, returns (False, [list of error messages])
        
        Raises:
            jsonschema.ValidationError: If strict_mode=True and validation fails
        """
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(entity))
        
        if errors:
            error_messages = [e.message for e in errors]
            if strict_mode:
                # Raise the first validation error in strict mode
                raise errors[0]
            return False, error_messages
        
        return True, []