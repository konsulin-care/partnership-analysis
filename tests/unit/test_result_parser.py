import pytest
from src.python.research.result_parser import parse_search_results, extract_structured_results


class TestResultParser:
    """Test suite for result parser functions."""

    def test_parse_search_results_normal_case(self):
        """Test parse_search_results with normal input."""
        search_results = [
            {
                "query": "test query 1",
                "results": [
                    {
                        "title": "Test Title 1",
                        "url": "https://example.com/1",
                        "snippet": "Test snippet 1",
                        "confidence": 0.9
                    },
                    {
                        "title": "Test Title 2",
                        "url": "https://example.com/2",
                        "snippet": "Test snippet 2"
                    }
                ]
            },
            {
                "query": "test query 2",
                "results": [
                    {
                        "title": "Test Title 3",
                        "url": "https://example.com/3",
                        "snippet": "Test snippet 3",
                        "confidence": 0.8
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert "parsed_results" in result
        assert "total_results" in result
        assert "queries_processed" in result

        assert result["queries_processed"] == 2
        assert result["total_results"] == 3
        assert len(result["parsed_results"]) == 3

        # Check first result
        first_result = result["parsed_results"][0]
        assert first_result["query"] == "test query 1"
        assert first_result["title"] == "Test Title 1"
        assert first_result["url"] == "https://example.com/1"
        assert first_result["snippet"] == "Test snippet 1"
        assert first_result["confidence"] == 0.9

        # Check second result (missing confidence, should default to 0.5)
        second_result = result["parsed_results"][1]
        assert second_result["confidence"] == 0.5

    def test_parse_search_results_empty_input(self):
        """Test parse_search_results with empty input."""
        result = parse_search_results([])

        assert result["parsed_results"] == []
        assert result["total_results"] == 0
        assert result["queries_processed"] == 0

    def test_parse_search_results_missing_fields(self):
        """Test parse_search_results with missing fields in results."""
        search_results = [
            {
                "query": "test query",
                "results": [
                    {
                        "title": "Test Title",
                        # missing url, snippet, confidence
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert len(result["parsed_results"]) == 1
        parsed = result["parsed_results"][0]
        assert parsed["title"] == "Test Title"
        assert parsed["url"] == ""  # default empty string
        assert parsed["snippet"] == ""  # default empty string
        assert parsed["confidence"] == 0.5 * 0.8 * 0.9  # default * invalid url * missing snippet

    def test_parse_search_results_invalid_url(self):
        """Test parse_search_results with invalid URL."""
        search_results = [
            {
                "query": "test query",
                "results": [
                    {
                        "title": "Test Title",
                        "url": "invalid-url",
                        "snippet": "Test snippet",
                        "confidence": 0.9
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert len(result["parsed_results"]) == 1
        parsed = result["parsed_results"][0]
        assert parsed["url"] == "invalid-url"
        assert parsed["confidence"] == 0.9 * 0.8  # Reduced for invalid URL

    def test_parse_search_results_missing_title_or_snippet(self):
        """Test parse_search_results with missing title or snippet."""
        search_results = [
            {
                "query": "test query",
                "results": [
                    {
                        "url": "https://example.com",
                        "snippet": "Test snippet",
                        "confidence": 0.9
                        # missing title
                    },
                    {
                        "title": "Test Title",
                        "url": "https://example.com",
                        "confidence": 0.9
                        # missing snippet
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert len(result["parsed_results"]) == 2

        # First result: missing title
        first = result["parsed_results"][0]
        assert first["title"] == ""
        assert first["confidence"] == 0.9 * 0.9  # Reduced for missing title

        # Second result: missing snippet
        second = result["parsed_results"][1]
        assert second["snippet"] == ""
        assert second["confidence"] == 0.9 * 0.9  # Reduced for missing snippet

    def test_parse_search_results_empty_results_list(self):
        """Test parse_search_results with empty results list."""
        search_results = [
            {
                "query": "test query",
                "results": []
            }
        ]

        result = parse_search_results(search_results)

        assert result["parsed_results"] == []
        assert result["total_results"] == 0
        assert result["queries_processed"] == 1

    def test_parse_search_results_multiple_queries_empty_results(self):
        """Test parse_search_results with multiple queries, some with empty results."""
        search_results = [
            {
                "query": "query 1",
                "results": [
                    {"title": "Title 1", "url": "https://ex1.com", "snippet": "Snippet 1", "confidence": 0.8}
                ]
            },
            {
                "query": "query 2",
                "results": []
            },
            {
                "query": "query 3",
                "results": [
                    {"title": "Title 2", "url": "https://ex2.com", "snippet": "Snippet 2", "confidence": 0.7}
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert result["queries_processed"] == 3
        assert result["total_results"] == 2
        assert len(result["parsed_results"]) == 2

    def test_parse_search_results_whitespace_handling(self):
        """Test parse_search_results with whitespace in fields."""
        search_results = [
            {
                "query": "  test query  ",
                "results": [
                    {
                        "title": "  Test Title  ",
                        "url": "  https://example.com  ",
                        "snippet": "  Test snippet  ",
                        "confidence": 0.9
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert len(result["parsed_results"]) == 1
        parsed = result["parsed_results"][0]
        assert parsed["query"] == "  test query  "  # query not stripped
        assert parsed["title"] == "Test Title"  # title stripped
        assert parsed["url"] == "https://example.com"  # url stripped
        assert parsed["snippet"] == "Test snippet"  # snippet stripped

    def test_parse_search_results_none_values(self):
        """Test parse_search_results with None values."""
        search_results = [
            {
                "query": None,
                "results": [
                    {
                        "title": None,
                        "url": None,
                        "snippet": None,
                        "confidence": None
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert len(result["parsed_results"]) == 1
        parsed = result["parsed_results"][0]
        assert parsed["query"] is None
        assert parsed["title"] == ""  # str(None) would be "None", but code uses .get("", "")
        assert parsed["url"] == ""
        assert parsed["snippet"] == ""
        assert parsed["confidence"] == 0.5 * 0.8 * 0.9  # default * invalid url * missing snippet

    def test_extract_structured_results_alias(self):
        """Test that extract_structured_results is an alias for parse_search_results."""
        search_results = [
            {
                "query": "test",
                "results": [
                    {"title": "Title", "url": "https://ex.com", "snippet": "Snippet", "confidence": 0.8}
                ]
            }
        ]

        parse_result = parse_search_results(search_results)
        extract_result = extract_structured_results(search_results)

        assert parse_result == extract_result

    def test_parse_search_results_large_input(self):
        """Test parse_search_results with large input."""
        # Create 100 queries with 10 results each
        search_results = []
        for i in range(100):
            results = []
            for j in range(10):
                results.append({
                    "title": f"Title {i}-{j}",
                    "url": f"https://example.com/{i}/{j}",
                    "snippet": f"Snippet {i}-{j}",
                    "confidence": 0.8
                })
            search_results.append({
                "query": f"Query {i}",
                "results": results
            })

        result = parse_search_results(search_results)

        assert result["queries_processed"] == 100
        assert result["total_results"] == 1000
        assert len(result["parsed_results"]) == 1000

    def test_parse_search_results_confidence_reduction_calculation(self):
        """Test confidence reduction calculations."""
        search_results = [
            {
                "query": "test",
                "results": [
                    {
                        "title": "Good Title",
                        "url": "https://example.com",
                        "snippet": "Good snippet",
                        "confidence": 1.0
                    },
                    {
                        "title": "",  # missing title
                        "url": "https://example.com",
                        "snippet": "Good snippet",
                        "confidence": 1.0
                    },
                    {
                        "title": "Good Title",
                        "url": "bad-url",  # invalid URL
                        "snippet": "Good snippet",
                        "confidence": 1.0
                    },
                    {
                        "title": "",  # missing title
                        "url": "bad-url",  # invalid URL
                        "snippet": "",  # missing snippet
                        "confidence": 1.0
                    }
                ]
            }
        ]

        result = parse_search_results(search_results)

        assert len(result["parsed_results"]) == 4

        # First: no reduction
        assert result["parsed_results"][0]["confidence"] == 1.0

        # Second: missing title (0.9 reduction)
        assert result["parsed_results"][1]["confidence"] == 1.0 * 0.9

        # Third: invalid URL (0.8 reduction)
        assert result["parsed_results"][2]["confidence"] == 1.0 * 0.8

        # Fourth: invalid URL (0.8) + missing title/snippet (0.9)
        expected = 1.0 * 0.8 * 0.9
        assert result["parsed_results"][3]["confidence"] == pytest.approx(expected)