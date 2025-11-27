"""
Entity normalization utilities for partnership analysis data.

This module provides the EntityNormalizer class for normalizing extracted entities
and calculated metrics to conform to the defined JSON schemas. It handles type coercion,
currency normalization, date formatting, and field mapping.
"""

import datetime
from typing import Dict, Any, List, Union


class EntityNormalizer:
    """
    Normalizer for mapping and coercing data types according to JSON schemas.

    Handles currency normalization (to IDR), date formatting (ISO standards),
    type coercion, and field mapping for partnership analysis entities.
    """

from typing import Dict, Any, List, Union, Optional

    def normalize_entity(
        self,
        entity: Dict[str, Any],
        schema: Dict[str, Any],
        field_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Normalize an entity dictionary according to the provided JSON schema.

        Args:
            entity: The raw entity data to normalize
            schema: The JSON schema defining the expected structure and types
            field_mapping: Optional mapping from entity keys to schema property names

        Returns:
            Normalized entity dictionary conforming to the schema
        """
        if field_mapping is None:
            field_mapping = {}

        normalized = {}
        properties = schema.get('properties', {})

        # First, apply field mapping to entity
        mapped_entity = self._apply_field_mapping(entity, field_mapping)

        for prop_name, prop_schema in properties.items():
            if prop_name in mapped_entity:
                value = mapped_entity[prop_name]
                normalized[prop_name] = self._normalize_value(value, prop_schema, prop_name)
            # Note: Required fields validation is handled separately by SchemaValidator

        return normalized

    def _apply_field_mapping(self, entity: Dict[str, Any], field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mapping to rename keys in the entity."""
        mapped = {}
        for key, value in entity.items():
            mapped_key = field_mapping.get(key, key)
            mapped[mapped_key] = value
        return mapped

    def _normalize_value(self, value: Any, schema: Dict[str, Any], field_name: str = "") -> Any:
        """
        Recursively normalize a value according to its schema definition.

        Args:
            value: The value to normalize
            schema: The schema for this value
            field_name: The field name (used for special handling like currency)

        Returns:
            Normalized value
        """
        schema_type = schema.get('type')

        if schema_type == 'string':
            normalized_value = self._normalize_string(value, schema)
        elif schema_type == 'number':
            normalized_value = self._normalize_number(value, field_name)
        elif schema_type == 'integer':
            normalized_value = self._normalize_integer(value, field_name)
        elif schema_type == 'boolean':
            normalized_value = self._normalize_boolean(value)
        elif schema_type == 'array':
            normalized_value = self._normalize_array(value, schema)
        elif schema_type == 'object':
            normalized_value = self._normalize_object(value, schema)
        else:
            # For unknown types, return as-is
            normalized_value = value

        return normalized_value

    def _normalize_string(self, value: Any, schema: Dict[str, Any]) -> str:
        """Normalize string values with format handling."""
        if not isinstance(value, str):
            value = str(value)

        format_type = schema.get('format')
        if format_type == 'date-time':
            value = self._format_datetime(value)
        elif format_type == 'date':
            value = self._format_date(value)
        elif format_type == 'email':
            value = value.strip().lower() if value else None
        elif format_type == 'uri':
            value = value.strip() if value else None

        return value

    def _normalize_number(self, value: Any, field_name: str = "") -> Union[float, None]:
        """Normalize number values with currency handling."""
        if value is None or value == "":
            return None

        if isinstance(value, str):
            # Remove common separators and convert
            clean_value = value.replace(',', '').replace(' ', '').strip()
            try:
                value = float(clean_value)
            except ValueError:
                return 0.0
        elif not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return 0.0

        # Currency normalization for IDR fields
        if field_name.endswith('_idr') and isinstance(value, (int, float)):
            value = self._normalize_currency(value, 'IDR')

        return value

    def _normalize_integer(self, value: Any, field_name: str = "") -> Union[int, None]:
        """Normalize integer values."""
        if value is None or value == "":
            return None

        if isinstance(value, str):
            clean_value = value.replace(',', '').replace(' ', '').strip()
            try:
                value = int(float(clean_value))
            except ValueError:
                return 0
        elif isinstance(value, float):
            value = int(value)
        elif not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return 0

        return value

    def _normalize_boolean(self, value: Any) -> bool:
        """Normalize boolean values."""
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    def _normalize_array(self, value: Any, schema: Dict[str, Any]) -> List[Any]:
        """Normalize array values."""
        if not isinstance(value, list):
            return []

        items_schema = schema.get('items')
        if items_schema:
            return [self._normalize_value(item, items_schema) for item in value]
        return value

    def _normalize_object(self, value: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize object values recursively."""
        if not isinstance(value, dict):
            return {}
        return self.normalize_entity(value, schema)

    def _format_datetime(self, value: str) -> str:
        """Format value to ISO datetime string."""
        if isinstance(value, datetime.datetime):
            if value.tzinfo:
                # Convert to UTC and format
                utc_value = value.astimezone(datetime.timezone.utc)
                return utc_value.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            else:
                return value.isoformat()
        elif isinstance(value, str):
            # Try to parse common formats and reformat
            try:
                # Handle Z suffix
                if value.endswith('Z'):
                    parsed = datetime.datetime.fromisoformat(value[:-1] + '+00:00')
                else:
                    parsed = datetime.datetime.fromisoformat(value)
                return parsed.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            except ValueError:
                # If can't parse, return as-is
                return value
        return value

    def _format_date(self, value: str) -> str:
        """Format value to YYYY-MM-DD date string."""
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, str):
            try:
                parsed = datetime.datetime.fromisoformat(value)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                return value
        return value

    def _normalize_currency(self, value: float, target_currency: str = 'IDR') -> float:
        """
        Normalize currency values to target currency.

        Currently only handles IDR, but extensible for other currencies.
        """
        # For now, assume all values are already in IDR or convert if needed
        # In future, could add exchange rate conversion
        if target_currency == 'IDR':
            return float(value)
        return float(value)