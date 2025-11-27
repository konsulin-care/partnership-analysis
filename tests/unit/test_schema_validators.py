import json
import pytest
import jsonschema
from src.python.schema.validators import SchemaValidator
from src.python.schema.base_schemas import (
    METADATA_SCHEMA,
    ORGANIZATIONS_SCHEMA,
    PARTNERSHIP_TERMS_SCHEMA,
    FINANCIAL_DATA_SCHEMA,
    FULL_SCHEMA
)


class TestSchemaValidator:
    """Test cases for SchemaValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a SchemaValidator instance."""
        return SchemaValidator()

    @pytest.fixture
    def validation_data(self):
        """Load validation test data."""
        with open("tests/fixtures/sample_schema_validation_data.json", "r") as f:
            return json.load(f)

    def test_validate_entity_against_schema_valid_metadata(self, validator, validation_data):
        """Test validation of valid metadata."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["valid_metadata_minimal"],
            METADATA_SCHEMA
        )
        assert is_valid is True
        assert errors == []

    def test_validate_entity_against_schema_invalid_metadata_missing_required(self, validator, validation_data):
        """Test validation of metadata missing required fields."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["invalid_metadata_missing_required"],
            METADATA_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("required" in error.lower() for error in errors)

    def test_validate_entity_against_schema_invalid_metadata_wrong_type(self, validator, validation_data):
        """Test validation of metadata with wrong field types."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["invalid_metadata_wrong_type"],
            METADATA_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("number" in error.lower() or "type" in error.lower() for error in errors)

    def test_validate_entity_against_schema_valid_organization(self, validator, validation_data):
        """Test validation of valid organization."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["valid_organization"],
            ORGANIZATIONS_SCHEMA
        )
        assert is_valid is True
        assert errors == []

    def test_validate_entity_against_schema_invalid_organization_missing_required(self, validator, validation_data):
        """Test validation of organization missing required fields."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["invalid_organization_missing_required"],
            ORGANIZATIONS_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("required" in error.lower() for error in errors)

    def test_validate_entity_against_schema_valid_partnership_terms(self, validator, validation_data):
        """Test validation of valid partnership terms."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["valid_partnership_terms"],
            PARTNERSHIP_TERMS_SCHEMA
        )
        assert is_valid is True
        assert errors == []

    def test_validate_entity_against_schema_invalid_partnership_terms_out_of_range(self, validator, validation_data):
        """Test validation of partnership terms with values out of range."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["invalid_partnership_terms_out_of_range"],
            PARTNERSHIP_TERMS_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        # Should have errors for revenue_share_pct > 100, minimum < 0, commitment_years < 1
        assert len(errors) >= 3

    def test_validate_entity_against_schema_valid_financial_scenario(self, validator, validation_data):
        """Test validation of valid financial scenario."""
        # Extract the scenario from the valid data
        scenario = validation_data["valid_financial_scenario"]
        scenario_schema = FINANCIAL_DATA_SCHEMA["properties"]["scenarios"]["items"]

        is_valid, errors = validator.validate_entity_against_schema(
            scenario,
            scenario_schema
        )
        assert is_valid is True
        assert errors == []

    def test_validate_entity_against_schema_valid_full_document(self, validator, validation_data):
        """Test validation of valid full document."""
        is_valid, errors = validator.validate_entity_against_schema(
            validation_data["valid_full_document"],
            FULL_SCHEMA
        )
        assert is_valid is True
        assert errors == []

    def test_validate_entity_against_schema_strict_mode_valid(self, validator, validation_data):
        """Test strict mode with valid data doesn't raise exception."""
        try:
            is_valid, errors = validator.validate_entity_against_schema(
                validation_data["valid_metadata_minimal"],
                METADATA_SCHEMA,
                strict_mode=True
            )
            assert is_valid is True
            assert errors == []
        except jsonschema.ValidationError:
            pytest.fail("Strict mode should not raise exception for valid data")

    def test_validate_entity_against_schema_strict_mode_invalid(self, validator, validation_data):
        """Test strict mode with invalid data raises ValidationError."""
        with pytest.raises(jsonschema.ValidationError):
            validator.validate_entity_against_schema(
                validation_data["invalid_metadata_missing_required"],
                METADATA_SCHEMA,
                strict_mode=True
            )

    def test_validate_entity_against_schema_schema_version_parameter(self, validator, validation_data):
        """Test that schema_version parameter is accepted (currently unused)."""
        # Should work the same regardless of schema_version
        is_valid1, errors1 = validator.validate_entity_against_schema(
            validation_data["valid_metadata"],
            METADATA_SCHEMA,
            schema_version="v1"
        )
        is_valid2, errors2 = validator.validate_entity_against_schema(
            validation_data["valid_metadata"],
            METADATA_SCHEMA,
            schema_version="v2"
        )

        assert is_valid1 == is_valid2
        assert errors1 == errors2

    def test_validate_entity_against_schema_empty_entity(self, validator):
        """Test validation of empty entity."""
        is_valid, errors = validator.validate_entity_against_schema(
            {},
            METADATA_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_entity_against_schema_none_entity(self, validator):
        """Test validation of None entity."""
        is_valid, errors = validator.validate_entity_against_schema(
            None,
            METADATA_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_entity_against_schema_invalid_schema(self, validator):
        """Test validation with invalid schema definition."""
        invalid_schema = {"type": "invalid_type"}
        # jsonschema raises UnknownType exception for invalid types
        with pytest.raises(jsonschema.exceptions.UnknownType):
            validator.validate_entity_against_schema(
                {"test": "value"},
                invalid_schema
            )

    def test_validate_entity_against_schema_nested_object_validation(self, validator):
        """Test validation of nested objects."""
        # Test organization with invalid nested location
        invalid_org = {
            "name": "Test Clinic",
            "role": "tenant",
            "location": {
                "city": "Jakarta",
                "country": "Indonesia",
                "coordinates": [106.8456]  # Only one coordinate, needs two
            }
        }

        is_valid, errors = validator.validate_entity_against_schema(
            invalid_org,
            ORGANIZATIONS_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        # Check that there are validation errors (exact message may vary)
        assert len(errors) >= 1

    def test_validate_entity_against_schema_enum_validation(self, validator):
        """Test validation of enum fields."""
        # Invalid role
        invalid_org = {
            "name": "Test Clinic",
            "role": "invalid_role"
        }

        is_valid, errors = validator.validate_entity_against_schema(
            invalid_org,
            ORGANIZATIONS_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("enum" in error.lower() or "role" in error.lower() for error in errors)

    def test_validate_entity_against_schema_pattern_validation(self, validator):
        """Test validation of pattern-constrained fields."""
        # Invalid document_id pattern
        invalid_metadata = {
            "document_id": "short",  # Too short, needs at least 8 chars
            "generated_at": "2025-11-27T10:00:00Z",
            "schema_version": "1.0"
        }

        is_valid, errors = validator.validate_entity_against_schema(
            invalid_metadata,
            METADATA_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        # Check that there are validation errors (exact message may vary)
        assert len(errors) >= 1

    def test_validate_entity_against_schema_format_validation(self, validator):
        """Test validation of format-constrained fields."""
        # Test with valid email
        valid_org = {
            "name": "Test Clinic",
            "role": "tenant",
            "contact": {
                "email": "test@example.com"
            }
        }

        is_valid, errors = validator.validate_entity_against_schema(
            valid_org,
            ORGANIZATIONS_SCHEMA
        )
        assert is_valid is True
        assert errors == []

    def test_validate_entity_against_schema_array_validation(self, validator):
        """Test validation of array fields."""
        # Test scenarios array with invalid item
        invalid_financial = {
            "scenarios": [
                {
                    "name": "invalid_scenario",  # Not in enum
                    "monthly_revenue_idr": 1000000,
                    "monthly_costs": {}
                }
            ]
        }

        is_valid, errors = validator.validate_entity_against_schema(
            invalid_financial,
            FINANCIAL_DATA_SCHEMA
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("enum" in error.lower() or "scenario" in error.lower() for error in errors)