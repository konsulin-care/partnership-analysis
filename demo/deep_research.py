#!/usr/bin/env python3
"""
Simple test script for DeepResearchEngine capability and results.
Run this script from the project root directory in the activated conda environment.
"""

import sys
import os
import json
from unittest.mock import MagicMock

sys.path.append('.')

from src.python.research.deep_research_engine import DeepResearchEngine
from src.python.research.cache_manager import CacheManager

def main():
    """Run a simple deep research test."""

    # Sample brand configuration (similar to test fixtures)
    brand_config = {
        "BRAND_NAME": "Glow Aesthetics Clinic",
        "BRAND_INDUSTRY": "medical_aesthetics",
        "BRAND_ADDRESS": "Jakarta, Indonesia",
        "BRAND_ABOUT": "Premium medical aesthetics clinic specializing in hair transplants, skincare treatments, and cosmetic procedures. Luxury positioning with cutting-edge technology and personalized care for middle to high-income individuals aged 25-55.",
        "HUB_LOCATION": "Surabaya, Indonesia"
    }

    print("Starting Deep Research Test")
    print("=" * 50)
    print(f"Brand: {brand_config['BRAND_NAME']}")
    print(f"Industry: {brand_config['BRAND_INDUSTRY']}")
    print(f"Location: {brand_config['BRAND_ADDRESS']}")
    print()

    try:
        # Initialize the deep research engine with mock cache to avoid cached results
        print("Initializing DeepResearchEngine...")
        mock_cache = MagicMock()
        mock_cache.get_cached_result.return_value = None  # Force fresh research
        mock_cache.cache = {}  # Empty cache dict

        engine = DeepResearchEngine(cache_manager=mock_cache)
        print("✓ Engine initialized successfully")
        print()

        # Conduct deep research
        print("Conducting deep research (this may take a few minutes)...")
        result = engine.conduct_deep_research(brand_config)
        print("✓ Deep research completed")
        print()

        # Display results
        print("RESULTS SUMMARY")
        print("=" * 50)
        print(f"Brand Hash: {result['brand_hash']}")
        print(f"Total Iterations: {result['total_iterations']}")
        print(f"Completed At: {result['completed_at']}")
        print()

        print("ITERATION DETAILS")
        print("-" * 30)
        for i, iteration in enumerate(result['iterations'], 1):
            print(f"Iteration {i}:")
            print(f"  Adjusted Queries: {len(iteration['adjusted_queries'])}")
            print(f"  Search Results: {len(iteration['search_results'])}")
            print(f"  Further Questions: {len(iteration['further_questions'])}")
            print(f"  Timestamp: {iteration['timestamp']}")
            print()

            if iteration['synthesis']:
                print(f"  Synthesis Preview: {iteration['synthesis'][:200]}...")
                print()

        print("FINAL SYNTHESIS")
        print("-" * 20)
        print(result['final_synthesis'])
        print()

        print("ALL FINDINGS COUNT")
        print("-" * 20)
        print(f"Total Search Results: {len(result['all_findings'])}")

        # Optional: Save full results to file
        output_file = "deep_research_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Full results saved to {output_file}")

        print("\n" + "=" * 50)
        print("TEST COMPLETED SUCCESSFULLY")

    except Exception as e:
        print(f"❌ Error during deep research: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())