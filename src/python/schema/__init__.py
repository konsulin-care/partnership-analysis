"""
JSON Schema Builder Module for creating generalized JSON schema for coded context and downstream systems.

This module provides components for mapping extracted entities and calculated metrics to normalized schema fields,
validating data conformance to partnership analysis schema, and generating schema documentation.
"""

from .base_schemas import (
    METADATA_SCHEMA,
    ORGANIZATIONS_SCHEMA,
    PARTNERSHIP_TERMS_SCHEMA,
    FINANCIAL_DATA_SCHEMA,
    RESEARCH_DATA_SCHEMA,
    QUALITY_FLAGS_SCHEMA,
    FULL_SCHEMA
)
from .validators import SchemaValidator
from .normalizer import EntityNormalizer
from .schema_docs_generator import SchemaDocsGenerator

__all__ = [
    'METADATA_SCHEMA',
    'ORGANIZATIONS_SCHEMA',
    'PARTNERSHIP_TERMS_SCHEMA',
    'FINANCIAL_DATA_SCHEMA',
    'RESEARCH_DATA_SCHEMA',
    'QUALITY_FLAGS_SCHEMA',
    'FULL_SCHEMA',
    'SchemaValidator',
    'EntityNormalizer',
    'SchemaDocsGenerator'
]