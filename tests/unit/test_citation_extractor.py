"""
Unit tests for citation_extractor module.
"""

import json
import pytest
from src.python.extractors.citation_extractor import (
    extract_source_citations,
    generate_bibtex_citations,
    _extract_publication_date,
    _extract_author,
    _classify_citation_type
)


@pytest.fixture
def sample_search_results():
    """Load sample search results from fixture."""
    with open('tests/fixtures/sample_search_results.json', 'r') as f:
        return json.load(f)


class TestExtractSourceCitations:
    """Test source citation extraction."""

    def test_extract_source_citations_from_sample(self, sample_search_results):
        """Test citation extraction from sample data."""
        citations = extract_source_citations(sample_search_results)

        assert isinstance(citations, list)
        assert len(citations) == len(sample_search_results)

        # Check first citation structure
        citation = citations[0]
        required_fields = ['title', 'url', 'domain', 'confidence', 'citation_type']
        for field in required_fields:
            assert field in citation

        assert citation['url'].startswith('http')
        assert citation['confidence'] > 0

    def test_extract_source_citations_empty_input(self):
        """Test with empty input."""
        citations = extract_source_citations([])
        assert citations == []

    def test_extract_source_citations_missing_fields(self):
        """Test with results missing required fields."""
        results = [{
            'title': 'Test Title',
            'snippet': 'Test snippet'
            # Missing url
        }]
        citations = extract_source_citations(results)
        assert citations == []  # Should skip invalid results


class TestExtractPublicationDate:
    """Test publication date extraction."""

    def test_extract_year_only(self):
        """Test extracting year from snippet."""
        snippet = "Report published in 2025 shows market growth."
        date = _extract_publication_date(snippet)
        assert date == "2025"

    def test_extract_month_year(self):
        """Test extracting month and year."""
        snippet = "January 2025 market analysis indicates..."
        date = _extract_publication_date(snippet)
        assert date == "January 2025"

    def test_extract_full_date(self):
        """Test extracting full date."""
        snippet = "Published on Jan 15, 2025 by the research team."
        date = _extract_publication_date(snippet)
        assert date == "Jan 15, 2025"

    def test_extract_no_date(self):
        """Test with no date in snippet."""
        snippet = "This report has no publication date mentioned."
        date = _extract_publication_date(snippet)
        assert date == ""


class TestExtractAuthor:
    """Test author extraction."""

    def test_extract_author_by_pattern(self):
        """Test extracting author using 'by' pattern."""
        snippet = "This report by John Smith shows interesting data."
        author = _extract_author(snippet, "Test Title")
        assert author == "John Smith"

    def test_extract_author_reports_pattern(self):
        """Test extracting author using reports pattern."""
        snippet = "Market Research Inc reports that..."
        author = _extract_author(snippet, "Test Title")
        assert author == "Market Research Inc"

    def test_extract_no_author(self):
        """Test with no author information."""
        snippet = "This is an anonymous report with no author mentioned."
        author = _extract_author(snippet, "Test Title")
        assert author == ""


class TestClassifyCitationType:
    """Test citation type classification."""

    def test_classify_academic(self):
        """Test academic citation classification."""
        assert _classify_citation_type("research.edu", "/study") == "academic"
        assert _classify_citation_type("university.ac.id", "/journal") == "academic"

    def test_classify_government(self):
        """Test government citation classification."""
        assert _classify_citation_type("gov.uk", "/report") == "government"
        assert _classify_citation_type("kemenkes.go.id", "/data") == "government"

    def test_classify_industry_report(self):
        """Test industry report classification."""
        assert _classify_citation_type("statista.com", "/report") == "industry_report"
        assert _classify_citation_type("ibisworld.com", "/analysis") == "industry_report"

    def test_classify_news(self):
        """Test news citation classification."""
        assert _classify_citation_type("bbc.co.uk", "/news") == "news"
        assert _classify_citation_type("cnn.com", "/article") == "news"

    def test_classify_company(self):
        """Test company citation classification."""
        assert _classify_citation_type("example.com", "/about") == "company"
        assert _classify_citation_type("corp.com", "/corporate") == "company"

    def test_classify_web_page_default(self):
        """Test default web page classification."""
        assert _classify_citation_type("example.com", "/page") == "web_page"


class TestGenerateBibtexCitations:
    """Test BibTeX citation generation."""

    def test_generate_bibtex_citations(self, sample_search_results):
        """Test BibTeX generation from citations."""
        citations = extract_source_citations(sample_search_results)
        bibtex = generate_bibtex_citations(citations)

        assert isinstance(bibtex, str)
        assert "@misc{web_1," in bibtex
        assert "title=" in bibtex
        assert "url=" in bibtex

    def test_generate_bibtex_empty(self):
        """Test BibTeX generation with empty citations."""
        bibtex = generate_bibtex_citations([])
        assert bibtex == ""