"""
Schema Documentation Generator for JSON Schema entities.

This module provides the SchemaDocsGenerator class for generating human-readable
documentation from JSON Schema definitions, including field descriptions, validation
rules, and structural details.
"""

from typing import Dict, Any, List


class SchemaDocsGenerator:
    """
    Generates readable documentation from JSON Schema definitions.

    This class provides methods to convert JSON Schema dictionaries into
    formatted documentation strings, including schema descriptions, field
    details, and validation constraints.
    """

    def generate_schema_docs(self, schema: Dict[str, Any], title: str = "Schema Documentation") -> str:
        """
        Generate readable documentation from a JSON Schema.

        Args:
            schema: The JSON Schema dictionary to document
            title: Title for the documentation

        Returns:
            Formatted documentation string in Markdown format
        """
        docs = [f"# {title}\n"]

        # Add top-level description if present
        if "description" in schema:
            docs.append(f"{schema['description']}\n")

        # Process the schema structure
        docs.append(self._process_schema(schema))

        return "\n".join(docs)

    def _process_schema(self, schema: Dict[str, Any], indent: int = 0) -> str:
        """
        Recursively process a schema section and generate documentation.

        Args:
            schema: Schema section to process
            indent: Current indentation level

        Returns:
            Formatted documentation for this schema section
        """
        lines = []
        indent_str = "  " * indent

        # Type information
        type_ = schema.get("type", "unknown")
        lines.append(f"{indent_str}**Type:** {type_}")

        # Description
        if "description" in schema:
            lines.append(f"{indent_str}**Description:** {schema['description']}")

        # Required fields
        if "required" in schema and isinstance(schema["required"], list):
            lines.append(f"{indent_str}**Required fields:** {', '.join(schema['required'])}")

        # Properties for objects
        if "properties" in schema and isinstance(schema["properties"], dict):
            lines.append(f"{indent_str}**Properties:**")
            for prop, prop_schema in schema["properties"].items():
                lines.append(f"{indent_str}- `{prop}`:")
                lines.append(self._process_schema(prop_schema, indent + 2))

        # Items for arrays
        if "items" in schema and isinstance(schema["items"], dict):
            lines.append(f"{indent_str}**Items:**")
            lines.append(self._process_schema(schema["items"], indent + 2))

        # Validation constraints
        constraints = []
        for key in ["minimum", "maximum", "minItems", "maxItems", "minLength", "maxLength"]:
            if key in schema:
                constraints.append(f"{key}: {schema[key]}")

        if "enum" in schema and isinstance(schema["enum"], list):
            constraints.append(f"enum: {', '.join(str(v) for v in schema['enum'])}")

        if "pattern" in schema:
            constraints.append(f"pattern: {schema['pattern']}")

        if "format" in schema:
            constraints.append(f"format: {schema['format']}")

        if constraints:
            lines.append(f"{indent_str}**Constraints:** {', '.join(constraints)}")

        return "\n".join(lines)