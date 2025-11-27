"""
Citation Extractor module for extracting and tracking source citations.

This module extracts source references, URLs, and citation metadata from search results
for proper attribution and bibliography generation.
"""

import re
from typing import List, Dict, Any
from urllib.parse import urlparse
from ..config import ConfigLoader

config = ConfigLoader()


def extract_source_citations(search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract source citations from search results.

    Creates structured citation data for bibliography generation and source attribution.

    Args:
        search_results: List of parsed search result dictionaries

    Returns:
        List of citation dictionaries with metadata
    """
    citations = []

    for result in search_results:
        title_raw = result.get('title', [])
        url_raw = result.get('url', [])
        snippet = result.get('snippet', '').strip()
        confidence = result.get('confidence', 0.5)

        # Handle title as list or string
        if isinstance(title_raw, list):
            title = ' '.join(title_raw).strip()
        else:
            title = str(title_raw).strip()

        # Handle url as list or string
        if isinstance(url_raw, list):
            url = url_raw[0].strip() if url_raw else ''
        else:
            url = str(url_raw).strip()

        if not url or not title:
            continue

        # Parse URL for domain and path
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            path = parsed_url.path
        except:
            domain = url
            path = ''

        # Extract publication date if present in snippet
        pub_date = _extract_publication_date(snippet)

        # Extract author/organization from snippet or title
        author = _extract_author(snippet, title)

        # Create citation entry
        citation = {
            'title': title,
            'url': url,
            'domain': domain,
            'path': path,
            'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet,  # Truncate long snippets
            'confidence': confidence,
            'publication_date': pub_date,
            'author': author,
            'access_date': None,  # Could add current timestamp
            'citation_type': _classify_citation_type(domain, path)
        }

        citations.append(citation)

    return citations


def _extract_publication_date(snippet: str) -> str:
    """
    Extract publication date from snippet.

    Looks for date patterns in the snippet.

    Args:
        snippet: Search result snippet

    Returns:
        Date string or empty string
    """
    # Date patterns: "2025", "January 2025", "Jan 15, 2025"
    # Order matters: more specific patterns first
    date_patterns = [
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
        r'\b(\d{4})\b'  # Year only - last to avoid matching parts of other dates
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, snippet, re.IGNORECASE)
        if matches:
            # Return the first match (most recent/primary date)
            match = matches[0]
            if isinstance(match, str):  # Single capture group (year)
                return match
            elif len(match) == 2:  # Month Year
                return f"{match[0]} {match[1]}"
            elif len(match) == 3:  # Month Day Year
                return f"{match[0]} {match[1]}, {match[2]}"

    return ''


def _extract_author(snippet: str, title: str) -> str:
    """
    Extract author or organization name from snippet or title.

    Args:
        snippet: Search result snippet
        title: Result title

    Returns:
        Author/organization name or empty string
    """
    # Look for "by [Author]" patterns
    author_patterns = [
        r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+reports?',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+study'
    ]

    # Check snippet first, then title
    for text_to_check in [snippet, title]:
        for pattern in author_patterns:
            matches = re.findall(pattern, text_to_check)
            if matches:
                # Return the first match
                return matches[0].strip()

    # Fallback: extract domain as organization
    return ''


def _classify_citation_type(domain: str, path: str) -> str:
    """
    Classify the type of citation based on domain and path.

    Args:
        domain: Website domain
        path: URL path

    Returns:
        Citation type classification
    """
    # Academic/research sources
    if any(academic in domain.lower() for academic in ['.edu', '.ac.', 'research', 'study', 'journal']):
        return 'academic'

    # Government sources
    if '.gov' in domain.lower() or '.go.' in domain.lower() or 'gov.' in domain.lower() or any(gov in domain.lower() for gov in ['government', 'ministry', 'kemen', 'depkes']):
        return 'government'

    # Industry reports
    if any(industry in domain.lower() for industry in ['statista', 'ibisworld', 'marketresearch', 'report', 'analysis']):
        return 'industry_report'

    # News/media
    if any(media in domain.lower() for media in ['news', 'times', 'post', 'journal', 'cnn', 'bbc']):
        return 'news'

    # Company websites
    if any(company in path.lower() for company in ['/about', '/company', '/corporate']):
        return 'company'

    # Default
    return 'web_page'


def generate_bibtex_citations(citations: List[Dict[str, Any]]) -> str:
    """
    Generate BibTeX formatted citations from citation data.

    Args:
        citations: List of citation dictionaries

    Returns:
        BibTeX formatted string
    """
    bibtex_entries = []

    for i, citation in enumerate(citations):
        # Create a simple BibTeX key
        key = f"web_{i+1}"

        title = citation.get('title', '').replace('{', '').replace('}', '')
        url = citation.get('url', '')
        author = citation.get('author', 'Unknown')
        year = citation.get('publication_date', '')[:4] if citation.get('publication_date') else ''

        # Basic BibTeX web entry
        bib_entry = f"@misc{{{key},\n"
        bib_entry += f"  title={{{title}}},\n"
        bib_entry += f"  author={{{author}}},\n"
        if year:
            bib_entry += f"  year={{{year}}},\n"
        bib_entry += f"  url={{{url}}},\n"
        bib_entry += f"  note={{Accessed: {citation.get('access_date', 'Unknown')}}}\n"
        bib_entry += "}\n"

        bibtex_entries.append(bib_entry)

    return "\n".join(bibtex_entries)