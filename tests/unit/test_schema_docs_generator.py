import pytest
from src.python.schema.schema_docs_generator import SchemaDocsGenerator


class TestSchemaDocsGenerator:
    def test_generate_schema_docs_simple_object(self):
        """Test generating docs for a simple object schema."""
        schema = {
            "type": "object",
            "description": "A simple test object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string", "description": "The name field"},
                "age": {"type": "integer", "minimum": 0, "maximum": 120}
            }
        }
        generator = SchemaDocsGenerator()
        docs = generator.generate_schema_docs(schema, "Test Schema")

        assert "# Test Schema" in docs
        assert "A simple test object" in docs
        assert "**Type:** object" in docs
        assert "**Required fields:** name" in docs
        assert "`name`:" in docs
        assert "**Type:** string" in docs
        assert "**Description:** The name field" in docs
        assert "`age`:" in docs
        assert "**Constraints:** minimum: 0, maximum: 120" in docs

    def test_generate_schema_docs_with_array(self):
        """Test generating docs for schema with array properties."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "description": "List of tags",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 10
                }
            }
        }
        generator = SchemaDocsGenerator()
        docs = generator.generate_schema_docs(schema)

        assert "**Items:**" in docs
        assert "**Type:** string" in docs
        assert "**Constraints:** minItems: 1, maxItems: 10" in docs

    def test_generate_schema_docs_with_enum(self):
        """Test generating docs for schema with enum values."""
        schema = {
            "type": "string",
            "enum": ["option1", "option2", "option3"],
            "description": "An enum field"
        }
        generator = SchemaDocsGenerator()
        docs = generator.generate_schema_docs(schema)

        assert "**Type:** string" in docs
        assert "**Description:** An enum field" in docs
        assert "**Constraints:** enum: option1, option2, option3" in docs

    def test_generate_schema_docs_nested_object(self):
        """Test generating docs for nested object schemas."""
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "description": "Address information",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string", "description": "City name"}
                    }
                }
            }
        }
        generator = SchemaDocsGenerator()
        docs = generator.generate_schema_docs(schema)

        assert "`address`:" in docs
        assert "**Description:** Address information" in docs
        assert "`street`:" in docs
        assert "`city`:" in docs
        assert "**Description:** City name" in docs

    def test_generate_schema_docs_empty_schema(self):
        """Test generating docs for minimal schema."""
        schema = {"type": "string"}
        generator = SchemaDocsGenerator()
        docs = generator.generate_schema_docs(schema)

        assert "# Schema Documentation" in docs
        assert "**Type:** string" in docs