"""
Integration tests for schema module working with calculations and extractors modules.

Tests end-to-end scenarios where extracted data is normalized and validated,
and calculation results are schema-compliant.
"""

import json
import pytest
from pathlib import Path

# Import modules under test
from src.python.extractors import extract_financial_data
from src.python.schema import EntityNormalizer, SchemaValidator, RESEARCH_DATA_SCHEMA, FINANCIAL_DATA_SCHEMA
from src.python.calculations import calculate_operational_costs, calculate_breakeven
from src.python.config import ConfigLoader


class TestSchemaCalculationsIntegration:
    """Integration tests for schema normalization with extractors and calculations."""

    @pytest.fixture
    def sample_search_results(self):
        """Load sample search results from fixtures."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_search_results.json"
        with open(fixture_path, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def config(self):
        """Load configuration for calculations."""
        config_loader = ConfigLoader()
        return config_loader

    @pytest.fixture
    def normalizer(self):
        """Create entity normalizer instance."""
        return EntityNormalizer()

    @pytest.fixture
    def validator(self):
        """Create schema validator instance."""
        return SchemaValidator()

    def test_extract_and_normalize_research_data(self, sample_search_results, normalizer, validator):
        """Test extracting financial data from search results and normalizing to research schema."""
        # Extract financial data from search results
        extracted_data = extract_financial_data(sample_search_results)

        # Transform extracted data into research_data structure
        research_data = {
            "market_benchmarks": []
        }

        for item in extracted_data:
            benchmark = {
                "category": item.get("metric", item.get("type", "unknown")),
                "value": item.get("value", item.get("min_value", 0)),
                "unit": item.get("currency", item.get("unit", "")),
                "source_citation": item.get("source", ""),
                "research_date": "2025-11-27",  # Current date for test
                "confidence": item.get("confidence", 0.5)
            }
            research_data["market_benchmarks"].append(benchmark)

        # Normalize the research data
        normalized_research = normalizer.normalize_entity(research_data, RESEARCH_DATA_SCHEMA)

        # Validate against schema
        is_valid, errors = validator.validate_entity_against_schema(
            normalized_research, RESEARCH_DATA_SCHEMA
        )

        assert is_valid, f"Research data validation failed: {errors}"
        assert len(normalized_research["market_benchmarks"]) > 0

    def test_calculations_with_extracted_data(self, sample_search_results, config, normalizer, validator):
        """Test running calculations using extracted benchmark data."""
        # Extract financial data
        extracted_data = extract_financial_data(sample_search_results)

        # Find pricing benchmark for revenue estimation
        revenue_estimate = 285_000_000  # Default fallback
        for item in extracted_data:
            if item.get("type") == "pricing_benchmark" and "clinic" in item.get("metric", "").lower():
                # Use average of min and max pricing as revenue estimate
                min_val = item.get("min_value", 0)
                max_val = item.get("max_value", 0)
                if min_val > 0 and max_val > 0:
                    revenue_estimate = (min_val + max_val) / 2
                    break

        # Run calculations for both standalone and hub models
        standalone_costs = calculate_operational_costs(revenue_estimate, "standalone", config)
        hub_costs = calculate_operational_costs(revenue_estimate, "hub", config)

        # Calculate breakeven for standalone model
        capex = config.get("standalone_capex", 200_000_000)
        monthly_profit = revenue_estimate - standalone_costs["total_operational_costs"]
        breakeven_months = calculate_breakeven(capex, monthly_profit) if monthly_profit > 0 else 0

        # Structure calculation results
        financial_data = {
            "scenarios": [
                {
                    "name": "standalone",
                    "monthly_revenue_idr": revenue_estimate,
                    "monthly_costs": {
                        "rent_idr": standalone_costs.get("rent", 0),
                        "staff_idr": standalone_costs.get("staff", 0),
                        "utilities_idr": standalone_costs.get("utilities", 0),
                        "medical_supplies_idr": standalone_costs.get("supplies", 0),
                        "capex_amortization_idr": capex / 36  # Assume 3-year amortization
                    },
                    "monthly_profit_idr": monthly_profit,
                    "annual_profit_idr": monthly_profit * 12,
                    "breakeven_months": breakeven_months
                },
                {
                    "name": "hub",
                    "monthly_revenue_idr": revenue_estimate,
                    "monthly_costs": {
                        "rent_idr": 0,  # Hub covers rent
                        "staff_idr": hub_costs.get("staff", 0),
                        "utilities_idr": hub_costs.get("utilities", 0),
                        "medical_supplies_idr": 0,  # Assume included
                        "capex_amortization_idr": (capex * 0.5) / 36  # Hub shares CAPEX
                    },
                    "monthly_profit_idr": revenue_estimate - hub_costs["total_operational_costs"],
                    "annual_profit_idr": (revenue_estimate - hub_costs["total_operational_costs"]) * 12,
                    "breakeven_months": calculate_breakeven(capex * 0.5, revenue_estimate - hub_costs["total_operational_costs"])
                }
            ],
            "year_1_revenue_idr": revenue_estimate * 12,
            "year_3_cumulative_savings_idr": (standalone_costs["total_operational_costs"] - hub_costs["total_operational_costs"]) * 36,
            "npv_discount_rate": config.get("discount_rate", 0.12)
        }

        # Normalize financial data
        normalized_financial = normalizer.normalize_entity(financial_data, FINANCIAL_DATA_SCHEMA)

        # Validate against schema
        is_valid, errors = validator.validate_entity_against_schema(
            normalized_financial, FINANCIAL_DATA_SCHEMA
        )

        assert is_valid, f"Financial data validation failed: {errors}"
        assert len(normalized_financial["scenarios"]) == 2
        assert all(scenario["monthly_revenue_idr"] > 0 for scenario in normalized_financial["scenarios"])

    def test_end_to_end_extraction_calculation_validation(
        self, sample_search_results, config, normalizer, validator
    ):
        """Test complete end-to-end flow: extract -> normalize -> calculate -> validate."""
        # Step 1: Extract data
        extracted_data = extract_financial_data(sample_search_results)

        # Step 2: Normalize research data
        research_data = {
            "market_benchmarks": [
                {
                    "category": item.get("metric", item.get("type", "unknown")),
                    "value": item.get("value", item.get("min_value", 0)),
                    "unit": item.get("currency", item.get("unit", "")),
                    "source_citation": item.get("source", ""),
                    "research_date": "2025-11-27",
                    "confidence": item.get("confidence", 0.5)
                }
                for item in extracted_data
            ]
        }

        normalized_research = normalizer.normalize_entity(research_data, RESEARCH_DATA_SCHEMA)

        # Step 3: Use extracted data for calculations
        revenue_estimate = 285_000_000
        for benchmark in normalized_research["market_benchmarks"]:
            if "clinic" in benchmark["category"].lower() and benchmark["unit"] == "IDR":
                revenue_estimate = benchmark["value"]
                break

        # Step 4: Run calculations and normalize results
        costs = calculate_operational_costs(revenue_estimate, "hub", config)
        profit = revenue_estimate - costs["total_operational_costs"]

        financial_data = {
            "scenarios": [
                {
                    "name": "hub",
                    "monthly_revenue_idr": revenue_estimate,
                    "monthly_costs": {
                        "rent_idr": 0,
                        "staff_idr": costs.get("staff", 0),
                        "utilities_idr": costs.get("utilities", 0),
                        "medical_supplies_idr": costs.get("supplies", 0),
                        "capex_amortization_idr": 5_555_556  # Example amortization
                    },
                    "monthly_profit_idr": profit,
                    "annual_profit_idr": profit * 12,
                    "breakeven_months": calculate_breakeven(200_000_000, profit)
                }
            ],
            "year_1_revenue_idr": revenue_estimate * 12,
            "year_3_cumulative_savings_idr": profit * 36,
            "npv_discount_rate": 0.12
        }

        normalized_financial = normalizer.normalize_entity(financial_data, FINANCIAL_DATA_SCHEMA)

        # Step 5: Validate both normalized structures
        research_valid, research_errors = validator.validate_entity_against_schema(
            normalized_research, RESEARCH_DATA_SCHEMA
        )
        financial_valid, financial_errors = validator.validate_entity_against_schema(
            normalized_financial, FINANCIAL_DATA_SCHEMA
        )

        assert research_valid, f"Research data validation failed: {research_errors}"
        assert financial_valid, f"Financial data validation failed: {financial_errors}"

        # Step 6: Verify data consistency
        assert normalized_financial["scenarios"][0]["monthly_revenue_idr"] == revenue_estimate
        assert normalized_research["market_benchmarks"][0]["confidence"] >= 0.0