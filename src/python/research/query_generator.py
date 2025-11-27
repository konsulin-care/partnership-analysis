"""
Query Generator module for creating targeted research queries.

This module generates search queries based on partner context for market research,
pricing benchmarks, operational costs, and competitive analysis.
"""

from typing import List


class QueryGenerator:
    """
    Generates targeted search queries for partnership analysis research.

    Based on partner type, industry, and location, this class creates
    specific queries for different research categories to gather market data.
    """

    def generate_research_queries(self, partner_type: str, industry: str, location: str) -> List[str]:
        """
        Generate a list of targeted search queries based on partner context.

        Args:
            partner_type: Type of partner (e.g., 'clinic', 'spa', 'wellness center')
            industry: Industry sector (e.g., 'medical aesthetics', 'wellness')
            location: Geographic location (e.g., 'Indonesia', 'Jakarta')

        Returns:
            List of search query strings, 2-3 per research category
        """
        queries = []

        # Category 1: Pricing and revenue benchmarks
        queries.extend([
            f"{industry} {partner_type} pricing {location} 2025",
            f"average revenue {industry} services {location}",
            f"{partner_type} pricing benchmarks {industry} {location}"
        ])

        # Category 2: Market growth and trends
        queries.extend([
            f"{industry} market growth rate {location} 2025",
            f"{partner_type} industry trends {location}",
            f"market size {industry} {location} forecast"
        ])

        # Category 3: Operational costs and expenses
        queries.extend([
            f"{partner_type} operational costs {industry} {location}",
            f"business expenses {industry} {location}",
            f"{partner_type} overhead costs {location}"
        ])

        # Category 4: Competitive landscape
        queries.extend([
            f"competitors {industry} {location}",
            f"{partner_type} competitive analysis {location}",
            f"market share {industry} {location}"
        ])

        return queries