import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from ..config.config_loader import ConfigLoader

class CacheManager:
    def __init__(self, config: Optional[ConfigLoader] = None):
        self.config = config or ConfigLoader()
        self.cache_file_path = self.config.get('CACHE_FILE_PATH', './cache/research_cache.json')
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load the research cache from JSON file."""
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
        """Return the default cache structure."""
        return {
            "cache_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "research_queries": {},
            "extracted_benchmarks": {}
        }

    def _save_cache(self):
        """Save the current cache to JSON file."""
        os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
        self.cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Failed to save cache file {self.cache_file_path}: {e}")

    def hash_query(self, query: str) -> str:
        """Generate a SHA256 hash for the query string."""
        return hashlib.sha256(query.encode('utf-8')).hexdigest()

    def get_cached_result(self, query_hash: str, ttl_days: int = 30) -> Optional[Dict[str, Any]]:
        """Retrieve cached result for a query hash if within TTL."""
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

    def cache_research_findings(self, query_hash: str, findings: Dict[str, Any], ttl_days: int = 30):
        """Cache research findings for a query hash."""
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

# Convenience functions
def hash_query(query: str) -> str:
    """Convenience function to hash a query."""
    manager = CacheManager()
    return manager.hash_query(query)

def get_cached_result(query_hash: str, ttl_days: int = 30) -> Optional[Dict[str, Any]]:
    """Convenience function to get cached result."""
    manager = CacheManager()
    return manager.get_cached_result(query_hash, ttl_days)

def cache_research_findings(query_hash: str, findings: Dict[str, Any], ttl_days: int = 30):
    """Convenience function to cache findings."""
    manager = CacheManager()
    manager.cache_research_findings(query_hash, findings, ttl_days)