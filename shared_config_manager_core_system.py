"""
Shared Configuration Manager - Improved Version
Fixed: Consistent lock ordering, deadlock prevention, improved thread safety
"""
from typing import Any, Dict, Optional
from threading import RLock
from pathlib import Path
import json
import time
import threading


class SharedConfigManager:
    """Thread-safe configuration manager with consistent lock ordering to prevent deadlocks."""

    _instance = None
    _lock = RLock()
    _lock_order_counter = 0

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._rules: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._main_lock = RLock()
        self._config_lock = RLock()
        self._rules_lock = RLock()
        self._metadata_lock = RLock()
        self._last_modified = 0
        self._lock_hierarchy = {
            '_main_lock': 1,
            '_config_lock': 2,
            '_rules_lock': 3,
            '_metadata_lock': 4
        }
        self._active_locks: Dict[int, str] = {}
        self._load_default_config()

    def _acquire_lock_with_order(self, lock_name: str) -> bool:
        max_attempts = 100
        attempt = 0
        while attempt < max_attempts:
            lock = getattr(self, lock_name, None)
            if lock is None:
                return False
            acquired = lock.acquire(timeout=0.1)
            if acquired:
                self._active_locks[threading.get_ident()] = lock_name
                return True
            time.sleep(0.001)
            attempt += 1
        return False

    def _release_lock(self, lock_name: str):
        lock = getattr(self, lock_name, None)
        if lock:
            try:
                lock.release()
                self._active_locks.pop(threading.get_ident(), None)
            except RuntimeError:
                pass

    def _load_default_config(self):
        self._config = {
            "system": {
                "max_concurrent_tasks": 10,
                "task_timeout_seconds": 300,
                "restart_delay_seconds": 5,
                "max_restart_attempts": 3
            },
            "optimization": {
                "analysis_interval_seconds": 10,
                "min_samples_for_analysis": 5,
                "max_optimization_rules": 100,
                "improvement_threshold": 0.05
            },
            "guardian": {
                "health_check_interval_seconds": 5,
                "process_monitor_interval_seconds": 2,
                "recovery_timeout_seconds": 30
            },
            "execution": {
                "batch_size": 5,
                "retry_attempts": 3,
                "progress_update_interval": 1
            },
            "logging": {
                "level": "INFO",
                "rotation": "100 MB",
                "retention": "7 days",
                "console_output": True
            }
        }

        self._rules = {
            "execution_sequence": ["validate", "prepare", "execute", "validate_result", "cleanup"],
            "optimization_triggers": ["slow_execution", "high_error_rate", "resource_bottleneck"],
            "recovery_strategies": {
                "process_crash": "restart_with_backoff",
                "timeout": "retry_with_alternate",
                "resource_exhaustion": "scale_down_and_retry"
            }
        }

        self._metadata = {
            "version": "1.0.1",
            "start_time": time.time(),
            "total_optimizations": 0,
            "total_tasks_completed": 0,
            "system_uptime": 0
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        with self._config_lock:
            value = self._config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value

    def set(self, key_path: str, value: Any):
        keys = key_path.split(".")
        with self._config_lock:
            target = self._config
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            target[keys[-1]] = value

    def get_rule(self, rule_key: str, default: Any = None) -> Any:
        keys = rule_key.split(".")
        with self._rules_lock:
            value = self._rules
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value

    def update_rule(self, rule_key: str, value: Any):
        with self._rules_lock:
            keys = rule_key.split(".")
            target = self._rules
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            target[keys[-1]] = value
        self.increment_stat("total_optimizations")

    def get_metadata(self) -> Dict[str, Any]:
        with self._metadata_lock:
            metadata = self._metadata.copy()
            metadata["system_uptime"] = time.time() - metadata["start_time"]
        return metadata

    def update_metadata(self, key: str, value: Any):
        with self._metadata_lock:
            self._metadata[key] = value

    def increment_stat(self, stat_name: str, increment: int = 1):
        with self._metadata_lock:
            current = self._metadata.get(stat_name, 0)
            self._metadata[stat_name] = current + increment

    def get_execution_rules(self) -> Dict[str, Any]:
        return self.get_rule("execution_sequence")

    def get_optimization_triggers(self) -> list:
        return self.get_rule("optimization_triggers", [])

    def get_recovery_strategy(self, error_type: str) -> str:
        strategies = self.get_rule("recovery_strategies", {})
        return strategies.get(error_type, "restart_with_backoff")

    def export_config(self) -> str:
        with self._main_lock:
            with self._config_lock:
                config_copy = self._config.copy()
            with self._rules_lock:
                rules_copy = self._rules.copy()
            with self._metadata_lock:
                metadata_copy = self._metadata.copy()
            return json.dumps({
                "config": config_copy,
                "rules": rules_copy,
                "metadata": metadata_copy
            }, indent=2)

    def import_config(self, config_json: str):
        data = json.loads(config_json)
        with self._config_lock:
            if "config" in data:
                self._config.update(data["config"])
        with self._rules_lock:
            if "rules" in data:
                self._rules.update(data["rules"])

    def get_all_optimization_rules(self) -> Dict[str, Any]:
        with self._rules_lock:
            return self._rules.copy()

    def reset_to_defaults(self):
        with self._main_lock:
            with self._config_lock:
                self._config = {}
            with self._rules_lock:
                self._rules = {}
            self._load_default_config()

    def increment_tasks_completed(self):
        """Thread-safe increment of completed tasks counter."""
        with self._metadata_lock:
            self._metadata["total_tasks_completed"] = self._metadata.get("total_tasks_completed", 0) + 1
