"""
Payload Validator Module

Validates Carbone JSON payloads before rendering to ensure compatibility
and prevent rendering failures.
"""

from typing import Dict, Any, List, Tuple
import structlog
from ..config.config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


class PayloadValidator:
    """
    Validates Carbone JSON payloads for rendering compatibility.

    This class provides methods to validate payload structure, required fields,
    and data integrity before sending to Carbone SDK.
    """

    def __init__(self, config: ConfigLoader):
        """
        Initialize the payload validator with configuration.

        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.required_payload_keys = {'data', 'template', 'options'}
        self.required_data_keys = {'document', 'executive_summary', 'partnership_overview',
                                   'financial_analysis', 'market_research', 'recommendations'}

    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete Carbone payload structure.

        Args:
            payload: Carbone payload dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check top-level structure
        if not isinstance(payload, dict):
            errors.append("Payload must be a dictionary")
            return False, errors

        # Check required keys
        missing_keys = self.required_payload_keys - set(payload.keys())
        if missing_keys:
            errors.append(f"Missing required payload keys: {missing_keys}")

        # Validate data section
        if 'data' in payload:
            data_valid, data_errors = self._validate_data_section(payload['data'])
            errors.extend(data_errors)

        # Validate template
        if 'template' in payload:
            template_valid, template_errors = self._validate_template(payload['template'])
            errors.extend(template_errors)

        # Validate options
        if 'options' in payload:
            options_valid, options_errors = self._validate_options(payload['options'])
            errors.extend(options_errors)

        is_valid = len(errors) == 0
        if is_valid:
            logger.debug("Payload validation passed")
        else:
            logger.warning("Payload validation failed", errors=errors)

        return is_valid, errors

    def _validate_data_section(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate the data section of the payload.

        Args:
            data: Data dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        if not isinstance(data, dict):
            errors.append("Data section must be a dictionary")
            return False, errors

        # Check for required data keys
        missing_data_keys = self.required_data_keys - set(data.keys())
        if missing_data_keys:
            errors.append(f"Missing required data keys: {missing_data_keys}")

        # Validate specific sections
        for section_name in self.required_data_keys:
            if section_name in data:
                section_valid, section_errors = self._validate_data_section_content(section_name, data[section_name])
                errors.extend(section_errors)

        return len(errors) == 0, errors

    def _validate_data_section_content(self, section_name: str, section_data: Any) -> Tuple[bool, List[str]]:
        """
        Validate content of a specific data section.

        Args:
            section_name: Name of the section being validated
            section_data: Data content to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        if section_data is None:
            errors.append(f"Section '{section_name}' cannot be None")
            return False, errors

        # Section-specific validations
        if section_name == 'document':
            if not isinstance(section_data, dict):
                errors.append("Document section must be a dictionary")
            elif not section_data.get('title'):
                errors.append("Document section must have a title")

        elif section_name == 'executive_summary':
            if not isinstance(section_data, dict):
                errors.append("Executive summary section must be a dictionary")

        elif section_name == 'partnership_overview':
            if not isinstance(section_data, dict):
                errors.append("Partnership overview section must be a dictionary")

        elif section_name == 'financial_analysis':
            if not isinstance(section_data, dict):
                errors.append("Financial analysis section must be a dictionary")

        elif section_name == 'market_research':
            if not isinstance(section_data, dict):
                errors.append("Market research section must be a dictionary")

        elif section_name == 'recommendations':
            if not isinstance(section_data, dict):
                errors.append("Recommendations section must be a dictionary")

        return len(errors) == 0, errors

    def _validate_template(self, template: str) -> Tuple[bool, List[str]]:
        """
        Validate template identifier.

        Args:
            template: Template identifier string

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        if not isinstance(template, str):
            errors.append("Template must be a string")
        elif not template.strip():
            errors.append("Template cannot be empty")
        elif len(template) > 100:
            errors.append("Template identifier too long (max 100 characters)")

        return len(errors) == 0, errors

    def _validate_options(self, options: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate rendering options.

        Args:
            options: Options dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        if not isinstance(options, dict):
            errors.append("Options must be a dictionary")
            return False, errors

        # Check for required options
        required_options = {'language', 'format'}
        missing_options = required_options - set(options.keys())
        if missing_options:
            errors.append(f"Missing required options: {missing_options}")

        # Validate format
        if 'format' in options and options['format'] != 'pdf':
            errors.append("Only 'pdf' format is supported")

        # Validate language
        if 'language' in options:
            supported_languages = self.config.get('supported_languages', ['en', 'id'])
            if options['language'] not in supported_languages:
                errors.append(f"Unsupported language: {options['language']}. Supported: {supported_languages}")

        # Validate margins if present
        if 'margins' in options:
            margins_valid, margins_errors = self._validate_margins(options['margins'])
            errors.extend(margins_errors)

        return len(errors) == 0, errors

    def _validate_margins(self, margins: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate margin settings.

        Args:
            margins: Margins dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        if not isinstance(margins, dict):
            errors.append("Margins must be a dictionary")
            return False, errors

        required_margins = {'top', 'bottom', 'left', 'right'}
        missing_margins = required_margins - set(margins.keys())
        if missing_margins:
            errors.append(f"Missing margin settings: {missing_margins}")

        for margin_name in required_margins:
            if margin_name in margins:
                value = margins[margin_name]
                if not isinstance(value, (int, float)):
                    errors.append(f"Margin '{margin_name}' must be a number")
                elif value < 0:
                    errors.append(f"Margin '{margin_name}' cannot be negative")
                elif value > 100:
                    errors.append(f"Margin '{margin_name}' too large (max 100)")

        return len(errors) == 0, errors

    def validate_and_suggest_fixes(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str], Dict[str, Any]]:
        """
        Validate payload and suggest fixes for common issues.

        Args:
            payload: Payload to validate and potentially fix

        Returns:
            Tuple of (is_valid, errors, fixes, suggested_payload)
            - is_valid: True if payload passes validation without fixes
            - errors: List of validation error messages
            - fixes: List of automatic fix messages applied
            - suggested_payload: Payload with fixes applied
        """
        is_valid, errors = self.validate_payload(payload)

        # Create a copy for suggestions
        suggested = payload.copy() if isinstance(payload, dict) else {}
        fixes = []

        # Apply common fixes
        if 'data' not in suggested:
            suggested['data'] = {}
            fixes.append("Added missing 'data' section")

        if 'template' not in suggested:
            suggested['template'] = self.config.get('carbone_template_id', 'partnership_report_v1')
            fixes.append("Added default template")

        if 'options' not in suggested:
            suggested['options'] = {
                'language': self.config.get('report_language', 'en'),
                'format': 'pdf',
                'margins': {
                    'top': self.config.get('pdf_margin_top', 20),
                    'bottom': self.config.get('pdf_margin_bottom', 20),
                    'left': self.config.get('pdf_margin_left', 15),
                    'right': self.config.get('pdf_margin_right', 15)
                }
            }
            fixes.append("Added default options")

        return is_valid, errors, fixes, suggested