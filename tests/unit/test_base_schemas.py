import pytest
from src.python.schema.base_schemas import (
    METADATA_SCHEMA,
    ORGANIZATIONS_SCHEMA,
    PARTNERSHIP_TERMS_SCHEMA,
    FINANCIAL_DATA_SCHEMA,
    RESEARCH_DATA_SCHEMA,
    QUALITY_FLAGS_SCHEMA,
    FULL_SCHEMA
)


class TestBaseSchemas:
    """Test cases for base schema definitions."""

    def test_metadata_schema_structure(self):
        """Test that metadata schema has correct structure."""
        assert isinstance(METADATA_SCHEMA, dict)
        assert METADATA_SCHEMA["type"] == "object"
        assert "required" in METADATA_SCHEMA
        assert "properties" in METADATA_SCHEMA

        required_fields = METADATA_SCHEMA["required"]
        assert "document_id" in required_fields
        assert "generated_at" in required_fields
        assert "schema_version" in required_fields

        properties = METADATA_SCHEMA["properties"]
        assert "document_id" in properties
        assert "document_hash" in properties
        assert "generated_at" in properties
        assert "schema_version" in properties
        assert "extraction_confidence" in properties

    def test_metadata_schema_constraints(self):
        """Test metadata schema field constraints."""
        properties = METADATA_SCHEMA["properties"]

        # document_id pattern
        doc_id_schema = properties["document_id"]
        assert doc_id_schema["pattern"] == r"^[a-z0-9_-]{8,}$"

        # document_hash pattern
        hash_schema = properties["document_hash"]
        assert hash_schema["pattern"] == r"^[a-f0-9]{32}$"

        # generated_at format
        assert properties["generated_at"]["format"] == "date-time"

        # schema_version enum
        version_schema = properties["schema_version"]
        assert "enum" in version_schema
        assert "1.0" in version_schema["enum"]
        assert "1.1" in version_schema["enum"]
        assert "2.0" in version_schema["enum"]

        # extraction_confidence range
        confidence_schema = properties["extraction_confidence"]
        assert confidence_schema["minimum"] == 0
        assert confidence_schema["maximum"] == 1

    def test_organizations_schema_structure(self):
        """Test organizations schema structure."""
        assert isinstance(ORGANIZATIONS_SCHEMA, dict)
        assert ORGANIZATIONS_SCHEMA["type"] == "object"
        assert "required" in ORGANIZATIONS_SCHEMA
        assert "properties" in ORGANIZATIONS_SCHEMA

        required_fields = ORGANIZATIONS_SCHEMA["required"]
        assert "name" in required_fields
        assert "role" in required_fields

        properties = ORGANIZATIONS_SCHEMA["properties"]
        assert "name" in properties
        assert "role" in properties
        assert "industry" in properties
        assert "location" in properties
        assert "contact" in properties

    def test_organizations_schema_role_enum(self):
        """Test organizations schema role enum values."""
        role_schema = ORGANIZATIONS_SCHEMA["properties"]["role"]
        assert "enum" in role_schema
        expected_roles = ["hub_operator", "tenant", "partner", "service_provider"]
        for role in expected_roles:
            assert role in role_schema["enum"]

    def test_organizations_schema_nested_objects(self):
        """Test organizations schema nested object structures."""
        location_schema = ORGANIZATIONS_SCHEMA["properties"]["location"]
        assert location_schema["type"] == "object"
        location_props = location_schema["properties"]
        assert "city" in location_props
        assert "country" in location_props
        assert "coordinates" in location_props

        # coordinates should be array with 2 items
        coords_schema = location_props["coordinates"]
        assert coords_schema["type"] == "array"
        assert coords_schema["minItems"] == 2
        assert coords_schema["maxItems"] == 2

        contact_schema = ORGANIZATIONS_SCHEMA["properties"]["contact"]
        assert contact_schema["type"] == "object"
        contact_props = contact_schema["properties"]
        assert "email" in contact_props
        assert "phone" in contact_props
        assert "website" in contact_props

        # email format
        assert contact_props["email"]["format"] == "email"
        # website format
        assert contact_props["website"]["format"] == "uri"

    def test_partnership_terms_schema_structure(self):
        """Test partnership terms schema structure."""
        assert isinstance(PARTNERSHIP_TERMS_SCHEMA, dict)
        assert PARTNERSHIP_TERMS_SCHEMA["type"] == "object"
        assert "required" in PARTNERSHIP_TERMS_SCHEMA
        assert "properties" in PARTNERSHIP_TERMS_SCHEMA

        required_fields = PARTNERSHIP_TERMS_SCHEMA["required"]
        assert "revenue_share_pct" in required_fields
        assert "capex_investment_idr" in required_fields
        assert "commitment_years" in required_fields

        properties = PARTNERSHIP_TERMS_SCHEMA["properties"]
        assert "revenue_share_pct" in properties
        assert "minimum_monthly_fee_idr" in properties
        assert "capex_investment_idr" in properties
        assert "capex_hub_contribution_idr" in properties
        assert "commitment_years" in properties
        assert "space_sqm" in properties
        assert "launch_timeline_days" in properties

    def test_partnership_terms_schema_constraints(self):
        """Test partnership terms schema field constraints."""
        properties = PARTNERSHIP_TERMS_SCHEMA["properties"]

        # revenue_share_pct range
        share_schema = properties["revenue_share_pct"]
        assert share_schema["minimum"] == 0
        assert share_schema["maximum"] == 100

        # minimum_monthly_fee_idr
        min_fee_schema = properties["minimum_monthly_fee_idr"]
        assert min_fee_schema["minimum"] == 0

        # commitment_years
        years_schema = properties["commitment_years"]
        assert years_schema["minimum"] == 1

        # space_sqm
        space_schema = properties["space_sqm"]
        assert space_schema["minimum"] == 1

        # launch_timeline_days
        timeline_schema = properties["launch_timeline_days"]
        assert timeline_schema["minimum"] == 30

    def test_financial_data_schema_structure(self):
        """Test financial data schema structure."""
        assert isinstance(FINANCIAL_DATA_SCHEMA, dict)
        assert FINANCIAL_DATA_SCHEMA["type"] == "object"
        assert "required" in FINANCIAL_DATA_SCHEMA
        assert "properties" in FINANCIAL_DATA_SCHEMA

        required_fields = FINANCIAL_DATA_SCHEMA["required"]
        assert "scenarios" in required_fields

        properties = FINANCIAL_DATA_SCHEMA["properties"]
        assert "scenarios" in properties
        assert "year_1_revenue_idr" in properties
        assert "year_3_cumulative_savings_idr" in properties
        assert "npv_discount_rate" in properties

    def test_financial_data_schema_scenarios_array(self):
        """Test financial data scenarios array structure."""
        scenarios_schema = FINANCIAL_DATA_SCHEMA["properties"]["scenarios"]
        assert scenarios_schema["type"] == "array"
        assert "items" in scenarios_schema

        scenario_item_schema = scenarios_schema["items"]
        assert scenario_item_schema["type"] == "object"

        scenario_required = scenario_item_schema["required"]
        assert "name" in scenario_required
        assert "monthly_revenue_idr" in scenario_required
        assert "monthly_costs" in scenario_required

        scenario_props = scenario_item_schema["properties"]
        assert "name" in scenario_props
        assert "monthly_revenue_idr" in scenario_props
        assert "monthly_costs" in scenario_props
        assert "monthly_profit_idr" in scenario_props
        assert "annual_profit_idr" in scenario_props
        assert "breakeven_months" in scenario_props

        # name enum
        name_schema = scenario_props["name"]
        assert "enum" in name_schema
        expected_scenarios = ["standalone", "hub", "optimistic", "conservative"]
        for scenario in expected_scenarios:
            assert scenario in name_schema["enum"]

        # monthly_costs object
        costs_schema = scenario_props["monthly_costs"]
        assert costs_schema["type"] == "object"
        costs_props = costs_schema["properties"]
        expected_costs = ["rent_idr", "staff_idr", "utilities_idr", "medical_supplies_idr", "capex_amortization_idr"]
        for cost in expected_costs:
            assert cost in costs_props

    def test_research_data_schema_structure(self):
        """Test research data schema structure."""
        assert isinstance(RESEARCH_DATA_SCHEMA, dict)
        assert RESEARCH_DATA_SCHEMA["type"] == "object"
        assert "properties" in RESEARCH_DATA_SCHEMA

        properties = RESEARCH_DATA_SCHEMA["properties"]
        assert "market_benchmarks" in properties

        benchmarks_schema = properties["market_benchmarks"]
        assert benchmarks_schema["type"] == "array"
        assert "items" in benchmarks_schema

        benchmark_item_schema = benchmarks_schema["items"]
        assert benchmark_item_schema["type"] == "object"

        benchmark_props = benchmark_item_schema["properties"]
        assert "category" in benchmark_props
        assert "value" in benchmark_props
        assert "unit" in benchmark_props
        assert "source_citation" in benchmark_props
        assert "research_date" in benchmark_props
        assert "confidence" in benchmark_props

        # research_date format
        assert benchmark_props["research_date"]["format"] == "date"

        # confidence range
        confidence_schema = benchmark_props["confidence"]
        assert confidence_schema["minimum"] == 0
        assert confidence_schema["maximum"] == 1

    def test_quality_flags_schema_structure(self):
        """Test quality flags schema structure."""
        assert isinstance(QUALITY_FLAGS_SCHEMA, dict)
        assert QUALITY_FLAGS_SCHEMA["type"] == "object"
        assert "properties" in QUALITY_FLAGS_SCHEMA

        properties = QUALITY_FLAGS_SCHEMA["properties"]
        assert "missing_data_fields" in properties
        assert "low_confidence_entities" in properties
        assert "data_inconsistencies" in properties

        # All should be arrays of strings
        for field in ["missing_data_fields", "low_confidence_entities", "data_inconsistencies"]:
            field_schema = properties[field]
            assert field_schema["type"] == "array"
            assert field_schema["items"]["type"] == "string"

    def test_full_schema_structure(self):
        """Test full schema combines all components correctly."""
        assert isinstance(FULL_SCHEMA, dict)
        assert "$schema" in FULL_SCHEMA
        assert FULL_SCHEMA["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert FULL_SCHEMA["title"] == "Partnership Analysis Context Schema"
        assert FULL_SCHEMA["type"] == "object"

        assert "required" in FULL_SCHEMA
        required_fields = FULL_SCHEMA["required"]
        assert "metadata" in required_fields
        assert "organizations" in required_fields
        assert "partnership_terms" in required_fields
        assert "financial_data" in required_fields

        properties = FULL_SCHEMA["properties"]
        assert "metadata" in properties
        assert "organizations" in properties
        assert "partnership_terms" in properties
        assert "financial_data" in properties
        assert "research_data" in properties
        assert "quality_flags" in properties

        # organizations should be array of organization objects
        orgs_schema = properties["organizations"]
        assert orgs_schema["type"] == "array"
        assert orgs_schema["items"] == ORGANIZATIONS_SCHEMA

        # Other properties should reference the individual schemas
        assert properties["metadata"] == METADATA_SCHEMA
        assert properties["partnership_terms"] == PARTNERSHIP_TERMS_SCHEMA
        assert properties["financial_data"] == FINANCIAL_DATA_SCHEMA
        assert properties["research_data"] == RESEARCH_DATA_SCHEMA
        assert properties["quality_flags"] == QUALITY_FLAGS_SCHEMA