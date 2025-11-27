import pytest
from src.python.research.query_generator import QueryGenerator


class TestQueryGenerator:
    """Test suite for QueryGenerator class."""

    def test_generate_research_queries_normal_case(self):
        """Test query generation with typical inputs."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="clinic",
            industry="medical aesthetics",
            location="Indonesia"
        )

        assert isinstance(queries, list)
        assert len(queries) == 12  # 4 categories * 3 queries each

        # Check that queries contain expected keywords
        assert any("medical aesthetics clinic pricing Indonesia 2025" in q for q in queries)
        assert any("average revenue medical aesthetics services Indonesia" in q for q in queries)
        assert any("medical aesthetics market growth rate Indonesia 2025" in q for q in queries)
        assert any("clinic operational costs medical aesthetics Indonesia" in q for q in queries)
        assert any("competitors medical aesthetics Indonesia" in q for q in queries)

    def test_generate_research_queries_empty_strings(self):
        """Test query generation with empty string inputs."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="",
            industry="",
            location=""
        )

        assert isinstance(queries, list)
        assert len(queries) == 12

        # Should still generate queries, even if they are generic
        assert all(isinstance(q, str) for q in queries)

    def test_generate_research_queries_special_characters(self):
        """Test query generation with special characters in inputs."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="wellness & spa",
            industry="health & beauty",
            location="New York, NY"
        )

        assert isinstance(queries, list)
        assert len(queries) == 12

        # Check that special characters are preserved
        assert any("wellness & spa" in q for q in queries)
        assert any("health & beauty" in q for q in queries)
        assert any("New York, NY" in q for q in queries)

    def test_generate_research_queries_unicode_characters(self):
        """Test query generation with Unicode characters."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="clinique",
            industry="médecine esthétique",
            location="Jakarta"
        )

        assert isinstance(queries, list)
        assert len(queries) == 12

        # Check that Unicode characters are preserved
        assert any("médecine esthétique" in q for q in queries)

    def test_generate_research_queries_long_inputs(self):
        """Test query generation with very long input strings."""
        generator = QueryGenerator()
        long_partner = "very long partner type name that might cause issues"
        long_industry = "extremely long industry sector name with many words"
        long_location = "a very long location name with multiple parts"

        queries = generator.generate_research_queries(
            partner_type=long_partner,
            industry=long_industry,
            location=long_location
        )

        assert isinstance(queries, list)
        assert len(queries) == 12

        # Check that long inputs are included
        assert any(long_partner in q for q in queries)
        assert any(long_industry in q for q in queries)
        assert any(long_location in q for q in queries)

    def test_generate_research_queries_numeric_inputs(self):
        """Test query generation with numeric inputs."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="clinic123",
            industry="industry2025",
            location="location456"
        )

        assert isinstance(queries, list)
        assert len(queries) == 12

        # Check that numeric inputs are included
        assert any("clinic123" in q for q in queries)
        assert any("industry2025" in q for q in queries)
        assert any("location456" in q for q in queries)

    def test_generate_research_queries_categories_structure(self):
        """Test that queries are structured by categories as expected."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="test_partner",
            industry="test_industry",
            location="test_location"
        )

        assert len(queries) == 12

        # First 3: pricing
        pricing_queries = queries[0:3]
        assert all("pricing" in q or "revenue" in q for q in pricing_queries)

        # Next 3: market growth
        growth_queries = queries[3:6]
        assert all("growth" in q or "market size" in q or "trends" in q for q in growth_queries)

        # Next 3: operational costs
        cost_queries = queries[6:9]
        assert all("costs" in q or "expenses" in q or "overhead" in q for q in cost_queries)

        # Last 3: competitive landscape
        comp_queries = queries[9:12]
        assert all("competitors" in q or "competitive" in q or "market share" in q for q in comp_queries)

    def test_generate_research_queries_no_duplicates(self):
        """Test that generated queries are unique."""
        generator = QueryGenerator()
        queries = generator.generate_research_queries(
            partner_type="clinic",
            industry="medical",
            location="Indonesia"
        )

        assert len(queries) == len(set(queries))  # No duplicates