"""
Permanent Guardian Service - Improved Version
Fixed: Enhanced error handling, improved recovery mechanisms, better event emission
"""
import time
import threading
import traceback
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
from loguru import logger
import psutil

from shared_config_manager_core_system import SharedConfigManager
from enhanced_logging_system_utility_module import EnhancedLoggingUtility


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class GuardianEvent:
    event_type: str
    timestamp: float
    details: str
    severity: str = "info"


class PermanentGuardianService:
    """Guardian Service with improved error handling and recovery mechanisms."""

    _instance = None
    _lock = threading.Lock()

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
        self.config = SharedConfigManager()
        self.log = EnhancedLoggingUtility()
        self._monitored_components: Dict[str, Callable] = {}
        self._component_status: Dict[str, HealthStatus] = {}
        self._component_errors: Dict[str, deque] = {}
        self._recovery_attempts: Dict[str, int] = {}
        self._last_health_check: Dict[str, float] = {}
        self._monitoring_active = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._event_listeners: List[Callable] = []
        self._event_history: deque = deque(maxlen=100)
        self._internal_lock = threading.RLock()
        self._status_lock = threading.Lock()
        self._health_check_interval = self.config.get("guardian.health_check_interval_seconds", 5)
        self._max_recovery_attempts = self.config.get("guardian.max_restart_attempts", 3)
        self._recovery_timeout = self.config.get("guardian.recovery_timeout_seconds", 30)
        self._recovery_queue: deque = deque(maxlen=50)
        self._error_threshold = 3
        self._consecutive_failures: Dict[str, int] = {}

    def register_component(self, name: str, health_check_func: Callable, auto_recover: bool = True):
        with self._internal_lock:
            self._monitored_components[name] = health_check_func
            self._component_status[name] = HealthStatus.HEALTHY
            self._component_errors[name] = deque(maxlen=20)
            self._recovery_attempts[name] = 0
            self._last_health_check[name] = time.time()
            self._consecutive_failures[name] = 0
        self.log.log_guardian_event("start", f"Component registered: {name}")

    def unregister_component(self, name: str):
        with self._internal_lock:
            for d in [self._monitored_components, self._component_status, self._component_errors,
                      self._recovery_attempts, self._last_health_check, self._consecutive_failures]:
                d.pop(name, None)
        self.log.info(f"Component unregistered: {name}")

    def start_guardian_loop(self):
        if self._monitoring_active:
            self.log.warning("Guardian loop already running")
            return
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._guardian_loop, daemon=True)
        self._monitoring_thread.start()
        self.log.log_guardian_event("start", "Guardian service activated")

    def stop_guardian_loop(self):
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        self.log.info("Guardian service stopped")

    def _guardian_loop(self):
        while self._monitoring_active:
            try:
                self._perform_health_checks()
                self._process_recovery_queue()
                self._dispatch_events()
                time.sleep(self._health_check_interval)
            except Exception as e:
                self.log.error(f"Guardian loop error: {e}")
                self._emit_event("guardian_loop_error", str(e), "critical")

    def _perform_health_checks(self):
        with self._internal_lock:
            component_names = list(self._monitored_components.keys())
        for name in component_names:
            self._check_component_health(name)

    def _check_component_health(self, name: str):
        check_func = self._monitored_components.get(name)
        if not check_func:
            return
        try:
            result = check_func()
            is_healthy = result if isinstance(result, bool) else (result is not False)

            with self._status_lock:
                if is_healthy:
                    if self._component_status.get(name) in [HealthStatus.FAILED, HealthStatus.RECOVERING]:
                        self.log.log_guardian_event("recovered", f"Component recovered: {name}")
                        self._emit_event("component_recovered", f"Component recovered: {name}", "info")
                    self._component_status[name] = HealthStatus.HEALTHY
                    self._recovery_attempts[name] = 0
                    self._consecutive_failures[name] = 0
                else:
                    self._component_status[name] = HealthStatus.DEGRADED
                    self._consecutive_failures[name] = self._consecutive_failures.get(name, 0) + 1

                if name in self._monitored_components:
                    self._last_health_check[name] = time.time()

        except Exception as e:
            self._handle_component_failure(name, e)

    def _handle_component_failure(self, name: str, error: Exception):
        error_msg = f"{type(error).__name__}: {str(error)}"
        stack_trace = traceback.format_exc()

        with self._status_lock:
            self._component_status[name] = HealthStatus.FAILED
            if name in self._component_errors:
                self._component_errors[name].append({
                    "timestamp": time.time(),
                    "error": error_msg,
                    "stack": stack_trace
                })
            self._recovery_attempts[name] = self._recovery_attempts.get(name, 0) + 1

        self.log.log_guardian_event("error", f"Component failure: {name} - {error_msg}")
        self._emit_event("component_failure", f"{name}: {error_msg}\n{stack_trace}", "critical")

        consecutive = self._consecutive_failures.get(name, 0)
        if consecutive >= self._error_threshold:
            self._initiate_recovery(name)

    def _initiate_recovery(self, name: str):
        with self._internal_lock:
            attempts = self._recovery_attempts.get(name, 0)
            if attempts > self._max_recovery_attempts:
                self._emit_event("recovery_exhausted", f"Max attempts reached for {name}", "critical")
                return
            self._component_status[name] = HealthStatus.RECOVERING

        self.log.log_guardian_event("restart", f"Initiating recovery for {name} (attempt {attempts})")
        recovery_strategy = self.config.get_recovery_strategy("process_crash")
        backoff_delay = min(2 ** attempts, self._recovery_timeout)

        with self._internal_lock:
            self._recovery_queue.append({
                "name": name,
                "attempt": attempts,
                "delay": backoff_delay,
                "strategy": recovery_strategy,
                "queued_at": time.time()
            })

    def _process_recovery_queue(self):
        with self._internal_lock:
            recoveries_to_process = []
            current_time = time.time()

            for item in list(self._recovery_queue):
                queued_time = item.get("queued_at", 0)
                delay = item.get("delay", 0)

                if current_time - queued_time >= delay:
                    recoveries_to_process.append(item)
                    try:
                        self._recovery_queue.remove(item)
                    except ValueError:
                        pass

        for recovery in recoveries_to_process:
            self._attempt_recovery(recovery["name"])

    def _attempt_recovery(self, name: str):
        try:
            check_func = self._monitored_components.get(name)
            if check_func:
                try:
                    result = check_func()
                    is_healthy = result if isinstance(result, bool) else (result is not False)
                except Exception:
                    is_healthy = False

                if is_healthy:
                    with self._status_lock:
                        self._component_status[name] = HealthStatus.HEALTHY
                        self._recovery_attempts[name] = 0
                        self._consecutive_failures[name] = 0
                    self.log.log_guardian_event("recovered", f"Recovery successful: {name}")
                    self._emit_event("recovery_success", f"Component recovered: {name}", "info")
                else:
                    self._initiate_recovery(name)
        except Exception as e:
            self.log.error(f"Recovery attempt failed for {name}: {e}")
            self._initiate_recovery(name)

    def _emit_event(self, event_type: str, details: str, severity: str):
        event = GuardianEvent(
            event_type=event_type,
            timestamp=time.time(),
            details=details,
            severity=severity
        )
        with self._internal_lock:
            self._event_history.append(event)

        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                self.log.error(f"Event listener error: {e}")

    def _dispatch_events(self):
        pass

    def add_event_listener(self, listener: Callable[[GuardianEvent], None]):
        with self._internal_lock:
            self._event_listeners.append(listener)

    def remove_event_listener(self, listener: Callable):
        with self._internal_lock:
            if listener in self._event_listeners:
                self._event_listeners.remove(listener)

    def get_system_health_summary(self) -> Dict[str, Any]:
        with self._status_lock:
            statuses = list(self._component_status.values())
            component_names = list(self._component_status.keys())

        healthy_count = sum(1 for s in statuses if s == HealthStatus.HEALTHY)
        degraded_count = sum(1 for s in statuses if s == HealthStatus.DEGRADED)
        failed_count = sum(1 for s in statuses if s == HealthStatus.FAILED)
        total = len(statuses) if statuses else 1

        overall = HealthStatus.HEALTHY
        if failed_count > 0:
            overall = HealthStatus.FAILED
        elif degraded_count > total * 0.3:
            overall = HealthStatus.DEGRADED

        return {
            "overall_status": overall.value,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "failed_count": failed_count,
            "total_components": total,
            "health_percentage": round(healthy_count / total * 100, 1),
            "timestamp": time.time()
        }

    def get_component_health(self, name: str) -> Optional[Dict[str, Any]]:
        with self._status_lock:
            if name not in self._component_status:
                return None
            status = self._component_status[name]
            errors = list(self._component_errors.get(name, []))[-5:]
            last_check = self._last_health_check.get(name, 0)
            attempts = self._recovery_attempts.get(name, 0)
            consecutive = self._consecutive_failures.get(name, 0)

        return {
            "name": name,
            "status": status.value,
            "recent_errors": [e.get("error", str(e)) for e in errors[-3:]],
            "last_health_check": last_check,
            "recovery_attempts": attempts,
            "consecutive_failures": consecutive,
            "time_since_check": time.time() - last_check if last_check > 0 else 0
        }

    def get_all_component_status(self) -> Dict[str, str]:
        with self._status_lock:
            return {name: status.value for name, status in self._component_status.items()}

    def get_guardian_events(self, event_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        with self._internal_lock:
            events = list(self._event_history)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return [
            {
                "type": e.event_type,
                "timestamp": e.timestamp,
                "details": e.details,
                "severity": e.severity
            }
            for e in events[-limit:]
        ]

    def force_component_recovery(self, name: str) -> bool:
        if name not in self._monitored_components:
            self.log.error(f"Cannot recover unknown component: {name}")
            return False
        with self._internal_lock:
            self._recovery_attempts[name] = 0
            self._consecutive_failures[name] = 0
        self.log.log_guardian_event("restart", f"Force recovery initiated: {name}")
        self._attempt_recovery(name)
        return True

    def get_process_statistics(self) -> Dict[str, Any]:
        try:
            process = psutil.Process()
            return {
                "pid": process.pid,
                "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "memory_percent": round(process.memory_percent(), 2),
                "num_threads": process.num_threads(),
                "status": process.status(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    def get_guardian_statistics(self) -> Dict[str, Any]:
        with self._internal_lock:
            total_events = len(self._event_history)
            critical_events = sum(1 for e in self._event_history if e.severity == "critical")
            warning_events = sum(1 for e in self._event_history if e.severity == "warning")

        return {
            "monitoring_active": self._monitoring_active,
            "monitored_components": len(self._monitored_components),
            "total_events": total_events,
            "critical_events": critical_events,
            "warning_events": warning_events,
            "event_listeners": len(self._event_listeners),
            "pending_recoveries": len(self._recovery_queue)
        }

    def reset_component_errors(self, name: str):
        with self._internal_lock:
            if name in self._component_errors:
                self._component_errors[name].clear()
            self._consecutive_failures[name] = 0
        self.log.info(f"Errors reset for component: {name}")

    def is_healthy(self) -> bool:
        with self._status_lock:
            if not self._monitoring_active:
                return False
            failed_count = sum(1 for s in self._component_status.values() if s == HealthStatus.FAILED)
            return failed_count == 0
