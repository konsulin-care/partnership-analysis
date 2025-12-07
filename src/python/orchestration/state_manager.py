"""
State management module for the orchestration layer.

This module provides cache and state management capabilities for
the orchestration workflow, including execution state tracking,
cache management, and error recovery.
"""

import json
import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
from datetime import datetime, timedelta
import threading

from src.python.config.config_loader import ConfigLoader
from src.python.orchestration.logger import Logger

class StateManager:
    """
    State manager for orchestration workflow.

    Handles execution state, caching, and persistence across
    workflow runs.
    """

    def __init__(self, config_loader: Optional[ConfigLoader] = None,
                 logger: Optional[Logger] = None):
        """
        Initialize the state manager.

        Args:
            config_loader: ConfigLoader instance for configuration
            logger: Logger instance for logging
        """
        self.config_loader = config_loader or ConfigLoader()
        self.logger = logger or Logger(self.config_loader)
        self._lock = threading.RLock()  # Use reentrant lock to allow recursive acquisition
        self._state_file = self._get_state_file_path()
        self._cache_file = self._get_cache_file_path()
        self._state = self._load_state()
        self._cache = self._load_cache()

    def _get_state_file_path(self) -> Path:
        """Get the path to the state file."""
        state_dir = Path(self.config_loader.get('STATE_DIR', 'state'))
        state_dir.mkdir(exist_ok=True)
        return state_dir / 'orchestration_state.json'

    def _get_cache_file_path(self) -> Path:
        """Get the path to the cache file."""
        cache_dir = Path(self.config_loader.get('CACHE_DIR', 'cache'))
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'orchestration_cache.json'

    def _load_state(self) -> Dict[str, Any]:
        """Load execution state from file."""
        if not self._state_file.exists():
            return self._get_default_state()

        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.log_error("state_load_error",
                                 f"Failed to load state: {str(e)}",
                                 {"file": str(self._state_file)})
            return self._get_default_state()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        if not self._cache_file.exists():
            return self._get_default_cache()

        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.log_error("cache_load_error",
                                 f"Failed to load cache: {str(e)}",
                                 {"file": str(self._cache_file)})
            return self._get_default_cache()

    def _get_default_state(self) -> Dict[str, Any]:
        """Get default state structure."""
        return {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'execution_history': [],
            'current_execution': None,
            'workflow_status': {}
        }

    def _get_default_cache(self) -> Dict[str, Any]:
        """Get default cache structure."""
        return {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'execution_cache': {},
            'research_cache': {},
            'calculation_cache': {}
        }

    def _save_state(self) -> None:
        """Save current state to file."""
        try:
            # Use timeout to prevent deadlocks
            acquired = self._lock.acquire(timeout=5.0)
            if not acquired:
                self.logger.log_error("state_save_error",
                                     "Failed to acquire lock for state save",
                                     {"file": str(self._state_file)})
                return

            try:
                self._state['last_updated'] = datetime.utcnow().isoformat()
                with open(self._state_file, 'w', encoding='utf-8') as f:
                    json.dump(self._state, f, indent=2, ensure_ascii=False)
            finally:
                self._lock.release()
        except IOError as e:
            self.logger.log_error("state_save_error",
                                 f"Failed to save state: {str(e)}",
                                 {"file": str(self._state_file)})

    def _save_cache(self) -> None:
        """Save current cache to file."""
        try:
            with self._lock:
                self._cache['last_updated'] = datetime.utcnow().isoformat()
                with open(self._cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except IOError as e:
            self.logger.log_error("cache_save_error",
                                 f"Failed to save cache: {str(e)}",
                                 {"file": str(self._cache_file)})

    def _generate_cache_key(self, *args: Any) -> str:
        """Generate a cache key from arguments."""
        key_str = ':'.join(str(arg) for arg in args)
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

    def start_execution(self, workflow_name: str, context: Dict[str, Any]) -> str:
        """
        Start a new workflow execution.

        Args:
            workflow_name: Name of the workflow
            context: Initial context for the execution

        Returns:
            Execution ID
        """
        execution_id = self._generate_cache_key(workflow_name, datetime.utcnow().isoformat())

        with self._lock:
            execution_record = {
                'execution_id': execution_id,
                'workflow_name': workflow_name,
                'start_time': datetime.utcnow().isoformat(),
                'status': 'started',
                'context': context,
                'stages': []
            }

            self._state['current_execution'] = execution_id
            self._state['execution_history'].append(execution_record)
            self._save_state()

        # Log execution start outside the lock to avoid potential deadlocks
        self.logger.log_execution_start(workflow_name, context)
        return execution_id

    def update_execution_stage(self, execution_id: str, stage_name: str,
                              status: str, data: Dict[str, Any]) -> None:
        """
        Update execution stage information.

        Args:
            execution_id: Execution ID
            stage_name: Name of the stage
            status: Status of the stage
            data: Data associated with the stage
        """
        with self._lock:
            # Find the execution record
            execution_record = None
            for record in self._state['execution_history']:
                if record['execution_id'] == execution_id:
                    execution_record = record
                    break

            if execution_record:
                stage_record = {
                    'stage_name': stage_name,
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': data
                }
                execution_record['stages'].append(stage_record)
                self._save_state()

        if execution_record:
            previous_stage_name = 'start'
            if len(execution_record['stages']) > 1:
                previous_stage_name = execution_record['stages'][-2]['stage_name']

            self.logger.log_stage_transition(
                execution_record['workflow_name'],
                previous_stage_name,
                stage_name,
                data
            )

    def end_execution(self, execution_id: str, status: str, metrics: Dict[str, Any]) -> None:
        """
        End a workflow execution.

        Args:
            execution_id: Execution ID
            status: Final status of execution
            metrics: Execution metrics
        """
        with self._lock:
            # Find and update the execution record
            for record in self._state['execution_history']:
                if record['execution_id'] == execution_id:
                    record['status'] = status
                    record['end_time'] = datetime.utcnow().isoformat()
                    record['metrics'] = metrics
                    break

            # Clear current execution if it matches
            if self._state['current_execution'] == execution_id:
                self._state['current_execution'] = None

            self._save_state()

        # Find the workflow name from the execution record
        workflow_name = 'unknown'
        for record in self._state['execution_history']:
            if record['execution_id'] == execution_id:
                workflow_name = record.get('workflow_name', 'unknown')
                break

        self.logger.log_execution_end(workflow_name, status, metrics)

    def cache_execution_result(self, execution_id: str, result: Dict[str, Any],
                              ttl_seconds: int = 86400) -> str:
        """
        Cache an execution result.

        Args:
            execution_id: Execution ID
            result: Result data to cache
            ttl_seconds: Time to live in seconds

        Returns:
            Cache key
        """
        cache_key = self._generate_cache_key(execution_id, 'execution_result')

        with self._lock:
            cache_entry = {
                'execution_id': execution_id,
                'result': result,
                'cached_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
                'ttl_seconds': ttl_seconds
            }

            self._cache['execution_cache'][cache_key] = cache_entry
            self._save_cache()

        return cache_key

    def get_cached_execution(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached execution result.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None if not found/expired
        """
        with self._lock:
            if cache_key not in self._cache['execution_cache']:
                return None

            cache_entry = self._cache['execution_cache'][cache_key]

            # Check if expired
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            if datetime.utcnow() > expires_at:
                del self._cache['execution_cache'][cache_key]
                self._save_cache()
                return None

            return cache_entry['result']

    def cache_research_result(self, query: str, result: Dict[str, Any],
                             ttl_seconds: int = 2592000) -> str:
        """
        Cache a research result.

        Args:
            query: Research query
            result: Research result data
            ttl_seconds: Time to live in seconds (default: 30 days)

        Returns:
            Cache key
        """
        cache_key = self._generate_cache_key(query, 'research')

        with self._lock:
            cache_entry = {
                'query': query,
                'result': result,
                'cached_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
                'ttl_seconds': ttl_seconds
            }

            self._cache['research_cache'][cache_key] = cache_entry
            self._save_cache()

        return cache_key

    def get_cached_research(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached research result.

        Args:
            query: Research query

        Returns:
            Cached research result or None if not found/expired
        """
        cache_key = self._generate_cache_key(query, 'research')

        with self._lock:
            if cache_key not in self._cache['research_cache']:
                return None

            cache_entry = self._cache['research_cache'][cache_key]

            # Check if expired
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            if datetime.utcnow() > expires_at:
                del self._cache['research_cache'][cache_key]
                self._save_cache()
                return None

            return cache_entry['result']

    def cache_calculation_result(self, calculation_type: str, params: Dict[str, Any],
                                result: Dict[str, Any], ttl_seconds: int = 86400) -> str:
        """
        Cache a calculation result.

        Args:
            calculation_type: Type of calculation
            params: Parameters used for calculation
            result: Calculation result
            ttl_seconds: Time to live in seconds

        Returns:
            Cache key
        """
        cache_key = self._generate_cache_key(calculation_type, str(params))

        with self._lock:
            cache_entry = {
                'calculation_type': calculation_type,
                'params': params,
                'result': result,
                'cached_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
                'ttl_seconds': ttl_seconds
            }

            self._cache['calculation_cache'][cache_key] = cache_entry
            self._save_cache()

        return cache_key

    def get_cached_calculation(self, calculation_type: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get a cached calculation result.

        Args:
            calculation_type: Type of calculation
            params: Parameters used for calculation

        Returns:
            Cached calculation result or None if not found/expired
        """
        cache_key = self._generate_cache_key(calculation_type, str(params))

        with self._lock:
            if cache_key not in self._cache['calculation_cache']:
                return None

            cache_entry = self._cache['calculation_cache'][cache_key]

            # Check if expired
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            if datetime.utcnow() > expires_at:
                del self._cache['calculation_cache'][cache_key]
                self._save_cache()
                return None

            return cache_entry['result']

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state.

        Returns:
            Current state dictionary
        """
        with self._lock:
            return self._state.copy()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        with self._lock:
            return {
                'execution_cache_size': len(self._cache['execution_cache']),
                'research_cache_size': len(self._cache['research_cache']),
                'calculation_cache_size': len(self._cache['calculation_cache']),
                'total_cache_entries': sum(len(cache) for cache in self._cache.values()
                                          if isinstance(cache, dict))
            }

    def clear_expired_cache(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of entries cleared
        """
        cleared_count = 0

        with self._lock:
            now = datetime.utcnow()

            # Clear expired execution cache
            expired_keys = []
            for key, entry in self._cache['execution_cache'].items():
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if now > expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache['execution_cache'][key]
                cleared_count += 1

            # Clear expired research cache
            expired_keys = []
            for key, entry in self._cache['research_cache'].items():
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if now > expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache['research_cache'][key]
                cleared_count += 1

            # Clear expired calculation cache
            expired_keys = []
            for key, entry in self._cache['calculation_cache'].items():
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if now > expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache['calculation_cache'][key]
                cleared_count += 1

            self._save_cache()

        return cleared_count

    def cleanup_old_state(self, max_history: int = 100) -> int:
        """
        Clean up old execution history.

        Args:
            max_history: Maximum number of execution records to keep

        Returns:
            Number of records removed
        """
        removed_count = 0

        with self._lock:
            if len(self._state['execution_history']) > max_history:
                # Keep the most recent records
                self._state['execution_history'] = self._state['execution_history'][-max_history:]
                removed_count = len(self._state['execution_history']) - max_history
                self._save_state()

        return removed_count