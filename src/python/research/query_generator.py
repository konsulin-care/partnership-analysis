"""
Query Generator module for creating targeted research queries.

This module generates search queries based on partner context for market research,
pricing benchmarks, operational costs, and competitive analysis.
"""

from typing import List, Dict, Any, Optional

from .llm_client import LLMClient


class QueryGenerator:
    """
    Generates targeted search queries for partnership analysis research.

    Based on partner type, industry, and location, this class creates
    specific queries for different research categories to gather market data.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the QueryGenerator with an optional LLM client.

        Args:
            llm_client: LLMClient instance for brand positioning extraction
        """
        self.llm_client = llm_client

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

    def generate_brand_research_queries(self, brand_config: Dict[str, Any]) -> List[str]:
        """
        Generate targeted research queries based on brand configuration.

        Extracts brand positioning from BRAND_ABOUT using LLM summarization,
        then generates queries for three research grounds:
        1. Brand performance (general, industry, vs competitors)
        2. Industry performance at brand location and hub location
        3. Competitive positioning based on brand positioning

        Args:
            brand_config: Dictionary containing brand information with keys:
                BRAND_NAME, BRAND_ABOUT, BRAND_ADDRESS, BRAND_INDUSTRY, HUB_LOCATION

        Returns:
            List of search query strings for brand research
        """
        if self.llm_client is None:
            self.llm_client = LLMClient()

        required_keys = ['BRAND_NAME', 'BRAND_ABOUT', 'BRAND_ADDRESS', 'BRAND_INDUSTRY', 'HUB_LOCATION']
        missing_keys = [k for k in required_keys if k not in brand_config]
        if missing_keys:
            raise ValueError(f"Missing required brand_config keys: {missing_keys}")

        brand_name = brand_config['BRAND_NAME']
        brand_about = brand_config['BRAND_ABOUT']
        brand_address = brand_config['BRAND_ADDRESS']
        brand_industry = brand_config['BRAND_INDUSTRY']
        hub_location = brand_config['HUB_LOCATION']

        # Extract brand positioning using LLM summarization
        positioning_prompt = f"""
        Summarize the brand positioning from this description: "{brand_about}".
        Provide a concise statement (1-2 sentences) about the brand's unique value proposition,
        target market, and competitive advantages in the {brand_industry} industry.
        """
        brand_positioning = self.llm_client.execute_prompt(
            'gemini-2.5-flash',
            positioning_prompt,
            temperature=0.3,
            max_tokens=256
        )

        queries = []

        # Ground 1: Brand performance (general, industry, vs competitors)
        queries.extend([
            f"{brand_name} performance {brand_industry} 2025",
            f"{brand_name} market share {brand_industry}",
            f"{brand_name} vs competitors {brand_industry}"
        ])

        # Ground 2: Industry performance at brand location and hub location
        queries.extend([
            f"{brand_industry} performance {brand_address} 2025",
            f"{brand_industry} market growth {hub_location}",
            f"{brand_industry} trends {brand_address} vs {hub_location}"
        ])

        # Ground 3: Competitive positioning based on brand positioning
        queries.extend([
            f"competitive positioning {brand_positioning} {brand_industry}",
            f"market analysis {brand_name} positioning {brand_industry}",
            f"competitors to {brand_name} {brand_industry} {brand_address}"
        ])

        return queries