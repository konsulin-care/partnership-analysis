"""
Cache Manager module for managing research result caching.

This module provides the CacheManager class that handles caching of research queries,
deep research results, and extracted benchmarks with TTL (time-to-live) support.
Supports both basic research caching and deep research iteration caching.
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List
from ..config.config_loader import ConfigLoader


class CacheManager:
    """
    Manages caching of research results and deep research iterations.

    Provides TTL-based caching for research queries, deep research results,
    and extracted benchmarks. Supports both basic research caching and
    iterative deep research caching with brand-specific organization.

    The cache structure includes:
    - research_queries: Basic query results with TTL
    - extracted_benchmarks: Processed benchmark data
    - deep_research: Iterative deep research results by brand hash

    Attributes:
        config: Configuration loader instance
        cache_file_path: Path to the JSON cache file
        cache: In-memory cache dictionary
    """

    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize the CacheManager with configuration.

        Args:
            config: ConfigLoader instance for loading cache file path and settings
        """
        self.config = config or ConfigLoader()
        self.cache_file_path = self.config.get('CACHE_FILE_PATH', './cache/research_cache.json')
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """
        Load the research cache from JSON file.

        Returns:
            Dictionary containing the cached data, or default structure if loading fails
        """
        if os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load cache file {self.cache_file_path}: {e}")
                return self._get_default_cache_structure()
        else:
            return self._get_default_cache_structure()

    def _get_default_cache_structure(self) -> Dict[str, Any]:
        """
        Return the default cache structure.

        Returns:
            Dictionary with default cache sections for research queries, benchmarks, and deep research
        """
        return {
            "cache_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "research_queries": {},
            "extracted_benchmarks": {},
            "deep_research": {}
        }

    def _save_cache(self) -> None:
        """
        Save the current cache to JSON file.

        Creates the cache directory if it doesn't exist. Updates the last_updated timestamp.
        """
        os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
        self.cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Failed to save cache file {self.cache_file_path}: {e}")

    def hash_query(self, query: str) -> str:
        """
        Generate a SHA256 hash for the query string.

        Args:
            query: The query string to hash

        Returns:
            Hexadecimal string representation of the SHA256 hash
        """
        return hashlib.sha256(query.encode('utf-8')).hexdigest()

    def get_cached_result(self, query_hash: str, ttl_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result for a query hash if within TTL.

        Args:
            query_hash: SHA256 hash of the query string
            ttl_days: Time-to-live in days (default: 30)

        Returns:
            Cached result dictionary if found and not expired, None otherwise.
            If expired, returns the stale result with 'stale': True flag.
        """
        if query_hash not in self.cache["research_queries"]:
            return None

        cached_item = self.cache["research_queries"][query_hash]
        cached_at_str = cached_item.get("cached_at")
        if not cached_at_str:
            return None

        try:
            cached_at = datetime.fromisoformat(cached_at_str.replace('Z', '+00:00'))
        except ValueError:
            return None

        now = datetime.now(timezone.utc)
        age_days = (now - cached_at).days

        if age_days > ttl_days:
            # Mark as stale but still return
            cached_item["stale"] = True
            return cached_item

        return cached_item

    def cache_research_findings(self, query_hash: str, findings: Dict[str, Any], ttl_days: int = 30) -> None:
        """
        Cache research findings for a query hash.

        Args:
            query_hash: SHA256 hash of the query string
            findings: Dictionary containing query, results, and synthesis
            ttl_days: Time-to-live in days (default: 30)
        """
        if "research_queries" not in self.cache:
            self.cache["research_queries"] = {}

        self.cache["research_queries"][query_hash] = {
            "query": findings.get("query", ""),
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_days": ttl_days,
            "results": findings.get("results", []),
            "synthesis": findings.get("synthesis", "")
        }
        self._save_cache()

    def cache_deep_research_result(self, brand_config_hash: str, iteration: int, results: Dict[str, Any], metadata: Dict[str, Any], ttl_days: int = 30) -> None:
        """
        Cache deep research results for a brand configuration hash and iteration.

        Args:
            brand_config_hash: Hash of the brand configuration
            iteration: Research iteration number
            results: Research results dictionary
            metadata: Additional metadata about the research
            ttl_days: Time-to-live in days (default: 30)
        """
        if "deep_research" not in self.cache:
            self.cache["deep_research"] = {}

        if brand_config_hash not in self.cache["deep_research"]:
            self.cache["deep_research"][brand_config_hash] = {}

        self.cache["deep_research"][brand_config_hash][str(iteration)] = {
            "results": results,
            "metadata": metadata,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_days": ttl_days
        }
        self._save_cache()

    def get_deep_research_result(self, brand_config_hash: str, iteration: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached deep research result for a brand config hash and optional iteration.

        Args:
            brand_config_hash: Hash of the brand configuration
            iteration: Specific iteration number, or None for latest iteration

        Returns:
            Cached deep research result if found and not expired, None otherwise.
            If expired, returns the stale result with 'stale': True flag.
        """
        if "deep_research" not in self.cache or brand_config_hash not in self.cache["deep_research"]:
            return None

        brand_cache = self.cache["deep_research"][brand_config_hash]

        if iteration is None:
            # Return the latest iteration
            if not brand_cache:
                return None
            latest_iteration = max(int(k) for k in brand_cache.keys())
            iteration = latest_iteration

        iteration_str = str(iteration)
        if iteration_str not in brand_cache:
            return None

        cached_item = brand_cache[iteration_str]
        cached_at_str = cached_item.get("cached_at")
        if not cached_at_str:
            return None

        try:
            cached_at = datetime.fromisoformat(cached_at_str.replace('Z', '+00:00'))
        except ValueError:
            return None

        now = datetime.now(timezone.utc)
        age_days = (now - cached_at).days

        if age_days > cached_item.get("ttl_days", 30):
            # Mark as stale but still return
            cached_item["stale"] = True
            return cached_item

        return cached_item

    def get_deep_research_iterations(self, brand_config_hash: str) -> List[int]:
        """
        Get list of available iterations for a brand config hash.

        Args:
            brand_config_hash: Hash of the brand configuration

        Returns:
            Sorted list of iteration numbers available in cache
        """
        if "deep_research" not in self.cache or brand_config_hash not in self.cache["deep_research"]:
            return []

        brand_cache = self.cache["deep_research"][brand_config_hash]
        return sorted([int(k) for k in brand_cache.keys()])

# Convenience functions for easy access without instantiating CacheManager

def hash_query(query: str) -> str:
    """
    Convenience function to hash a query string.

    Args:
        query: The query string to hash

    Returns:
        SHA256 hash of the query as a hexadecimal string
    """
    manager = CacheManager()
    return manager.hash_query(query)

def get_cached_result(query_hash: str, ttl_days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get cached research result.

    Args:
        query_hash: SHA256 hash of the query
        ttl_days: Time-to-live in days (default: 30)

    Returns:
        Cached result dictionary if found and valid, None otherwise
    """
    manager = CacheManager()
    return manager.get_cached_result(query_hash, ttl_days)

def cache_research_findings(query_hash: str, findings: Dict[str, Any], ttl_days: int = 30) -> None:
    """
    Convenience function to cache research findings.

    Args:
        query_hash: SHA256 hash of the query
        findings: Dictionary containing query results and synthesis
        ttl_days: Time-to-live in days (default: 30)
    """
    manager = CacheManager()
    manager.cache_research_findings(query_hash, findings, ttl_days)

def cache_deep_research_result(brand_config_hash: str, iteration: int, results: Dict[str, Any], metadata: Dict[str, Any], ttl_days: int = 30) -> None:
    """
    Convenience function to cache deep research results.

    Args:
        brand_config_hash: Hash of the brand configuration
        iteration: Research iteration number
        results: Research results dictionary
        metadata: Additional metadata about the research
        ttl_days: Time-to-live in days (default: 30)
    """
    manager = CacheManager()
    manager.cache_deep_research_result(brand_config_hash, iteration, results, metadata, ttl_days)

def get_deep_research_result(brand_config_hash: str, iteration: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get cached deep research result.

    Args:
        brand_config_hash: Hash of the brand configuration
        iteration: Specific iteration number, or None for latest

    Returns:
        Cached deep research result if found and valid, None otherwise
    """
    manager = CacheManager()
    return manager.get_deep_research_result(brand_config_hash, iteration)

def get_deep_research_iterations(brand_config_hash: str) -> List[int]:
    """
    Convenience function to get available deep research iterations.

    Args:
        brand_config_hash: Hash of the brand configuration

    Returns:
        Sorted list of iteration numbers available in cache
    """
    manager = CacheManager()
    return manager.get_deep_research_iterations(brand_config_hash)