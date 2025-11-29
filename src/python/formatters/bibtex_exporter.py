"""
BibTeX Exporter Module

Generates BibTeX bibliography from research data market benchmarks for academic
and professional citation management.
"""

import os
from typing import Dict, Any, List
from ..config.config_loader import ConfigLoader


def generate_bibtex(
    normalized_data: Dict[str, Any],
    config: ConfigLoader
) -> str:
    """
    Generate BibTeX bibliography from research data.

    Creates BibTeX entries from market benchmarks and research sources for
    proper citation and reference management.

    Args:
        normalized_data: Normalized partnership analysis data
        config: Configuration loader instance

    Returns:
        Path to the exported BibTeX file

    Raises:
        ValueError: If research data is missing or invalid
        OSError: If file cannot be written
    """
    try:
        # Extract research data
        research_data = normalized_data.get('research_data', {})
        benchmarks = research_data.get('market_benchmarks', [])

        if not benchmarks:
            # Create empty bibliography if no benchmarks
            bibtex_content = "% No market benchmarks available\n"
        else:
            # Generate BibTeX entries
            bibtex_entries = []
            for i, benchmark in enumerate(benchmarks, 1):
                entry = _create_bibtex_entry(benchmark, i)
                bibtex_entries.append(entry)

            bibtex_content = "\n\n".join(bibtex_entries) + "\n"

        # Export to file
        output_dir = config.get('output_dir', 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        bib_path = os.path.join(output_dir, 'references.bib')

        with open(bib_path, 'w', encoding='utf-8') as f:
            f.write(bibtex_content)

        return bib_path

    except Exception as e:
        raise OSError(f"Failed to generate BibTeX: {e}") from e


def _create_bibtex_entry(benchmark: Dict[str, Any], index: int) -> str:
    """
    Create a BibTeX entry from a benchmark.

    Args:
        benchmark: Market benchmark data
        index: Entry index for unique key

    Returns:
        Formatted BibTeX entry string
    """
    # Generate unique key
    category = benchmark.get('category', 'unknown').replace('_', '').replace(' ', '')
    key = f"benchmark{index}_{category}"

    # Extract fields
    title = benchmark.get('source_citation', 'Market Research Data')
    year = _extract_year(benchmark.get('research_date', ''))
    note = _format_benchmark_note(benchmark)

    # Build BibTeX entry
    entry_lines = [
        f"@misc{{{key},",
        f"  title={{{title}}},",
        f"  year={{{year}}},",
        f"  note={{{note}}}"
        "}"
    ]

    return "\n".join(entry_lines)


def _extract_year(date_string: str) -> str:
    """
    Extract year from date string.

    Args:
        date_string: Date string (ISO format or similar)

    Returns:
        Year as string, or current year if extraction fails
    """
    try:
        if not date_string:
            return "2025"
        year = date_string.split('-')[0] if '-' in date_string else date_string
        if year.isdigit():
            return year
        return "2025"  # Default fallback
    except (ValueError, IndexError):
        return "2025"


def _format_benchmark_note(benchmark: Dict[str, Any]) -> str:
    """
    Format benchmark data as BibTeX note.

    Args:
        benchmark: Benchmark data

    Returns:
        Formatted note string
    """
    category = benchmark.get('category', '').replace('_', ' ').title()
    value = benchmark.get('value', '')
    unit = benchmark.get('unit', '').replace('_', ' ')
    confidence = benchmark.get('confidence', 0)

    note_parts = [f"Category: {category}"]

    if value != '':
        note_parts.append(f"Value: {value}")

    if unit:
        note_parts.append(f"Unit: {unit}")

    if confidence >= 0:
        note_parts.append(f"Confidence: {confidence:.2f}")

    return "; ".join(note_parts)