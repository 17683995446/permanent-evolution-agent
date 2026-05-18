"""
Improved Execution Data Collector
Fixed: Thread safety with fine-grained locking, lock ordering consistency
"""
import time
import psutil
import threading
from typing import Dict, List, Optional, Any
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from shared_config_manager_core_system import SharedConfigManager
from enhanced_logging_system_utility_module import EnhancedLoggingUtility


@dataclass
class ExecutionMetrics:
    """Execution metrics data class."""
    task_id: str
    task_type: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    step_timings: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, status: str = "success", error: Optional[str] = None):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        if error:
            self.error = error


class ExecutionDataCollector:
    """Collects and analyzes execution data in real-time with improved thread safety."""

    def __init__(self):
        self.config = SharedConfigManager()
        self.log = EnhancedLoggingUtility()
        self._metrics_buffer: deque = deque(maxlen=1000)
        self._task_metrics: Dict[str, ExecutionMetrics] = {}
        self._system_metrics: deque = deque(maxlen=500)
        self._metrics_lock = threading.Lock()
        self._task_lock = threading.Lock()
        self._system_lock = threading.Lock()
        self._collection_active = False
        self._collection_thread: Optional[threading.Thread] = None
        self._min_samples = self.config.get("optimization.min_samples_for_analysis", 5)

    @contextmanager
    def _safe_lock(self, lock_type: str = "metrics"):
        lock_map = {
            "metrics": self._metrics_lock,
            "task": self._task_lock,
            "system": self._system_lock
        }
        lock = lock_map.get(lock_type, self._metrics_lock)
        acquired = lock.acquire(timeout=5.0)
        if not acquired:
            raise TimeoutError(f"Failed to acquire {lock_type} lock")
        try:
            yield
        finally:
            lock.release()

    def start_collection(self):
        """Start real-time data collection."""
        if self._collection_active:
            return
        self._collection_active = True
        self._collection_thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        self._collection_thread.start()
        self.log.log_guardian_event("start", "Execution data collection started")

    def stop_collection(self):
        """Stop data collection."""
        self._collection_active = False
        if self._collection_thread:
            self._collection_thread.join(timeout=2)

    def _collect_system_metrics(self):
        """Background thread for system metrics collection."""
        while self._collection_active:
            try:
                metrics = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    "net_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
                }
                with self._system_lock:
                    self._system_metrics.append(metrics)
                time.sleep(1)
            except Exception as e:
                self.log.error(f"System metrics collection error: {e}")
                time.sleep(5)

    def start_task(self, task_id: str, task_type: str, metadata: Optional[Dict] = None) -> ExecutionMetrics:
        """Start tracking a task execution."""
        metrics = ExecutionMetrics(
            task_id=task_id,
            task_type=task_type,
            start_time=time.time(),
            metadata=metadata or {}
        )
        with self._task_lock:
            self._task_metrics[task_id] = metrics
        self.log.debug(f"Task started tracking: {task_id}")
        return metrics

    def complete_task(self, task_id: str, status: str = "success", error: Optional[str] = None):
        """Complete task tracking."""
        with self._task_lock:
            if task_id in self._task_metrics:
                metrics = self._task_metrics[task_id]
                metrics.complete(status, error)
                with self._metrics_lock:
                    self._metrics_buffer.append(metrics)
                self.log.debug(f"Task completed: {task_id} ({status})")

    def record_step(self, task_id: str, step_name: str, duration: float):
        """Record individual step timing within a task."""
        with self._task_lock:
            if task_id in self._task_metrics:
                self._task_metrics[task_id].step_timings[step_name] = duration

    def update_resource_usage(self, task_id: str, usage: Dict[str, float]):
        """Update resource usage for a task."""
        with self._task_lock:
            if task_id in self._task_metrics:
                self._task_metrics[task_id].resource_usage.update(usage)

    def get_recent_metrics(self, count: int = 50) -> List[ExecutionMetrics]:
        """Get recent execution metrics."""
        with self._metrics_lock:
            return list(self._metrics_buffer)[-count:]

    def get_task_metrics(self, task_id: str) -> Optional[ExecutionMetrics]:
        """Get metrics for specific task."""
        with self._task_lock:
            return self._task_metrics.get(task_id)

    def get_average_duration(self, task_type: Optional[str] = None) -> float:
        """Calculate average execution duration."""
        with self._metrics_lock:
            metrics_list = list(self._metrics_buffer)
        if task_type:
            metrics_list = [m for m in metrics_list if m.task_type == task_type and m.duration]
        if not metrics_list:
            return 0.0
        return sum(m.duration for m in metrics_list if m.duration) / len(metrics_list)

    def get_success_rate(self, task_type: Optional[str] = None) -> float:
        """Calculate success rate."""
        with self._metrics_lock:
            metrics_list = list(self._metrics_buffer)
        if task_type:
            metrics_list = [m for m in metrics_list if m.task_type == task_type]
        if not metrics_list:
            return 1.0
        successful = sum(1 for m in metrics_list if m.status == "success")
        return successful / len(metrics_list)

    def get_error_analysis(self) -> Dict[str, Any]:
        """Analyze errors from recent executions."""
        with self._metrics_lock:
            recent = list(self._metrics_buffer)[-100:]
        errors = [m for m in recent if m.status == "failure" and m.error]
        error_types = {}
        for error in errors:
            error_key = error.error[:50] if error.error else "unknown"
            error_types[error_key] = error_types.get(error_key, 0) + 1
        return {
            "total_errors": len(errors),
            "error_types": error_types,
            "error_rate": len(errors) / len(recent) if recent else 0
        }

    def get_step_analysis(self) -> Dict[str, Dict[str, float]]:
        """Analyze step timings across tasks."""
        with self._task_lock:
            all_tasks = list(self._task_metrics.values())
        step_stats = {}
        for metrics in all_tasks:
            for step, duration in metrics.step_timings.items():
                if step not in step_stats:
                    step_stats[step] = {"durations": [], "count": 0}
                step_stats[step]["durations"].append(duration)
                step_stats[step]["count"] += 1
        result = {}
        for step, data in step_stats.items():
            durations = data["durations"]
            result[step] = {
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "count": data["count"]
            }
        return result

    def get_bottleneck_analysis(self) -> Dict[str, Any]:
        """Identify performance bottlenecks."""
        step_analysis = self.get_step_analysis()
        bottlenecks = []
        if step_analysis:
            avg_total = sum(s["avg"] for s in step_analysis.values())
            for step, stats in step_analysis.items():
                percentage = (stats["avg"] / avg_total * 100) if avg_total > 0 else 0
                if percentage > 20:
                    bottlenecks.append({
                        "step": step,
                        "avg_duration": stats["avg"],
                        "percentage": percentage,
                        "severity": "high" if percentage > 40 else "medium"
                    })
        return {
            "bottlenecks": sorted(bottlenecks, key=lambda x: x["percentage"], reverse=True),
            "total_steps_analyzed": len(step_analysis)
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics."""
        with self._system_lock:
            recent = list(self._system_metrics)[-10:] if self._system_metrics else []
        if not recent:
            return {"status": "unknown", "details": {}}
        avg_cpu = sum(m["cpu_percent"] for m in recent) / len(recent)
        avg_memory = sum(m["memory_percent"] for m in recent) / len(recent)
        status = "healthy"
        if avg_cpu > 80 or avg_memory > 80:
            status = "warning"
        if avg_cpu > 95 or avg_memory > 95:
            status = "critical"
        return {
            "status": status,
            "details": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "samples": len(recent)
            }
        }

    def has_sufficient_data(self) -> bool:
        """Check if there's enough data for meaningful analysis."""
        with self._metrics_lock:
            return len(self._metrics_buffer) >= self._min_samples

    def get_full_analysis(self) -> Dict[str, Any]:
        """Get comprehensive execution analysis."""
        return {
            "metrics_summary": {
                "total_tasks": len(self._metrics_buffer),
                "avg_duration": self.get_average_duration(),
                "success_rate": self.get_success_rate()
            },
            "error_analysis": self.get_error_analysis(),
            "step_analysis": self.get_step_analysis(),
            "bottleneck_analysis": self.get_bottleneck_analysis(),
            "system_health": self.get_system_health(),
            "has_sufficient_data": self.has_sufficient_data()
        }

    def clear_old_data(self, before_timestamp: Optional[float] = None):
        """Clear old metrics data."""
        if before_timestamp is None:
            before_timestamp = time.time() - 3600
        with self._metrics_lock:
            self._metrics_buffer = deque(
                [m for m in self._metrics_buffer if m.start_time >= before_timestamp],
                maxlen=1000
            )
        with self._task_lock:
            self._task_metrics = {
                k: v for k, v in self._task_metrics.items()
                if v.start_time >= before_timestamp
            }
