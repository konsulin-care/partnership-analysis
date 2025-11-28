"""
Base schema definitions for partnership analysis entities.

This module defines the base JSON schemas for each entity type used in the
partnership analysis system. These schemas are derived from the JSON Schema v1
template and ensure compatibility with the normalized output structure.
"""

from typing import Dict, Any

# Metadata schema
METADATA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["document_id", "generated_at", "schema_version"],
    "properties": {
        "document_id": {"type": "string", "pattern": "^[a-z0-9_-]{8,}$"},
        "document_hash": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
        "generated_at": {"type": "string", "format": "date-time"},
        "schema_version": {"type": "string", "enum": ["1.0", "1.1", "2.0"]},
        "extraction_confidence": {"type": "number", "minimum": 0, "maximum": 1}
    }
}

# Organizations schema (for array items)
ORGANIZATIONS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["name", "role"],
    "properties": {
        "name": {"type": "string"},
        "role": {"enum": ["hub_operator", "tenant", "partner", "service_provider"]},
        "industry": {"type": "string"},
        "location": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "country": {"type": "string"},
                "coordinates": {"type": "array", "minItems": 2, "maxItems": 2}
            }
        },
        "contact": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string"},
                "website": {"type": "string", "format": "uri"}
            }
        }
    }
}

# Partnership terms schema
PARTNERSHIP_TERMS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["revenue_share_pct", "capex_investment_idr", "commitment_years"],
    "properties": {
        "revenue_share_pct": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Percentage of monthly revenue paid as occupancy cost"
        },
        "minimum_monthly_fee_idr": {
            "type": "number",
            "minimum": 0,
            "description": "Floor cost if revenue share drops below threshold"
        },
        "capex_investment_idr": {
            "type": "number",
            "description": "Tenant CAPEX requirement medical equipment, renovation"
        },
        "capex_hub_contribution_idr": {
            "type": "number",
            "description": "Hub co-investment technology, infrastructure"
        },
        "commitment_years": {"type": "integer", "minimum": 1},
        "space_sqm": {"type": "number", "minimum": 1},
        "launch_timeline_days": {"type": "integer", "minimum": 30}
    }
}

# Financial data schema
FINANCIAL_DATA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["scenarios"],
    "properties": {
        "scenarios": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "monthly_revenue_idr", "monthly_costs"],
                "properties": {
                    "name": {"enum": ["standalone", "hub", "optimistic", "conservative"]},
                    "monthly_revenue_idr": {"type": "number", "minimum": 0},
                    "monthly_costs": {
                        "type": "object",
                        "properties": {
                            "rent_idr": {"type": "number"},
                            "staff_idr": {"type": "number"},
                            "utilities_idr": {"type": "number"},
                            "medical_supplies_idr": {"type": "number"},
                            "capex_amortization_idr": {"type": "number"}
                        }
                    },
                    "monthly_profit_idr": {"type": "number"},
                    "annual_profit_idr": {"type": "number"},
                    "breakeven_months": {"type": "integer", "minimum": 0}
                }
            }
        },
        "year_1_revenue_idr": {"type": "number"},
        "year_3_cumulative_savings_idr": {"type": "number"},
        "npv_discount_rate": {"type": "number", "minimum": 0, "maximum": 1}
    }
}

# Research data schema
RESEARCH_DATA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "market_benchmarks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "value": {"type": "number"},
                    "unit": {"type": "string"},
                    "source_citation": {"type": "string"},
                    "research_date": {"type": "string", "format": "date"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        }
    }
}

# Quality flags schema
QUALITY_FLAGS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "missing_data_fields": {"type": "array", "items": {"type": "string"}},
        "low_confidence_entities": {"type": "array", "items": {"type": "string"}},
        "data_inconsistencies": {"type": "array", "items": {"type": "string"}}
    }
}

# Full schema combining all entities
FULL_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Partnership Analysis Context Schema",
    "type": "object",
    "required": ["metadata", "organizations", "partnership_terms", "financial_data"],
    "properties": {
        "metadata": METADATA_SCHEMA,
        "organizations": {
            "type": "array",
            "items": ORGANIZATIONS_SCHEMA
        },
        "partnership_terms": PARTNERSHIP_TERMS_SCHEMA,
        "financial_data": FINANCIAL_DATA_SCHEMA,
        "research_data": RESEARCH_DATA_SCHEMA,
        "quality_flags": QUALITY_FLAGS_SCHEMA
    }
}