"""
Main Loop Controller
主循环控制器 - 协调四层运转，双并行调度，异常隔离处理。
协调所有层级的运转，保持执行与优化双并行运转，永久循环不停歇。
"""
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import signal
import sys

from shared_config_manager_core_system import SharedConfigManager
from enhanced_logging_system_utility_module import EnhancedLoggingUtility
from execution_data_collector_system_module import ExecutionDataCollector
from permanent_guardian_service_monitor_layer import PermanentGuardianService
from task_execution_engine_core_module import TaskExecutionEngine
from intelligent_optimizer_module_system_layer import IntelligentOptimizerModule
from sync_implementation_layer_core_system import SyncImplementationLayer


@dataclass
class LoopStatistics:
    total_cycles: int = 0
    total_tasks_completed: int = 0
    total_optimizations: int = 0
    start_time: float = field(default_factory=time.time)
    last_cycle_time: float = 0
    avg_cycle_duration: float = 0


class MainLoopController:
    """主循环控制器 - 四层协调运转，永久循环不停歇。"""

    def __init__(self):
        self.config = SharedConfigManager()
        self.log = EnhancedLoggingUtility()
        self.data_collector: Optional[ExecutionDataCollector] = None
        self.guardian_service: Optional[PermanentGuardianService] = None
        self.execution_engine: Optional[TaskExecutionEngine] = None
        self.optimizer_module: Optional[IntelligentOptimizerModule] = None
        self.sync_layer: Optional[SyncImplementationLayer] = None
        
        self._is_running = False
        self._main_loop_thread: Optional[threading.Thread] = None
        self._control_lock = threading.Lock()
        self._statistics = LoopStatistics()
        self._status_callbacks: List[Callable] = []
        self._shutdown_requested = False
        self._cycle_interval = 0.5
        self._last_status_report = 0.0

    def initialize(self):
        """初始化所有组件。"""
        self.log.section_divider("Permanent Evolution Agent Initialization")
        
        self.log.header("Initializing Data Collector...")
        self.data_collector = ExecutionDataCollector()
        self.data_collector.start_collection()
        
        self.log.header("Initializing Guardian Service...")
        self.guardian_service = PermanentGuardianService()
        self.guardian_service.start_guardian_loop()
        
        self.log.header("Initializing Task Execution Engine...")
        self.execution_engine = TaskExecutionEngine(self.data_collector)
        self.execution_engine.initialize()
        self.guardian_service.register_component(
            "execution_engine",
            self.execution_engine.is_healthy
        )
        
        self.log.header("Initializing Optimizer Module...")
        self.optimizer_module = IntelligentOptimizerModule(self.data_collector)
        self.optimizer_module.start_optimization_loop()
        self._setup_optimization_callback()
        self.guardian_service.register_component(
            "optimizer_module",
            self.optimizer_module.is_healthy if hasattr(self.optimizer_module, 'is_healthy') else lambda: True
        )
        
        self.log.header("Initializing Sync Layer...")
        self.sync_layer = SyncImplementationLayer()
        self.sync_layer.initialize()
        self.guardian_service.register_component(
            "sync_layer",
            self.sync_layer.is_healthy
        )
        
        self._setup_signal_handlers()
        self.log.success("All components initialized successfully")
        self.log.log_guardian_event("start", "Permanent Evolution Agent started")

    def _setup_optimization_callback(self):
        """设置优化回调 - 优化成果自动同步到执行层。"""
        def on_optimization_applied(optimization):
            if self.sync_layer:
                self.sync_layer.push_optimization(optimization)
            self._statistics.total_optimizations += 1
        
        self.optimizer_module.add_optimization_callback(on_optimization_applied)

    def _setup_signal_handlers(self):
        """设置信号处理器。"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理终止信号。"""
        self.log.warning(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_requested = True

    def start(self):
        """启动主循环。"""
        if self._is_running:
            self.log.warning("Main loop already running")
            return
        
        self._is_running = True
        self._main_loop_thread = threading.Thread(target=self._main_loop, daemon=True)
        self._main_loop_thread.start()
        self.log.section_divider("Permanent Evolution Agent - Running")
        self._display_startup_info()

    def _display_startup_info(self):
        """显示启动信息。"""
        metadata = self.config.get_metadata()
        self.log.display_panel(
            f"[bold]Agent Version:[/bold] {metadata.get('version', '1.0.0')}\n"
            f"[bold]Start Time:[/bold] {datetime.fromtimestamp(metadata.get('start_time', time.time())).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"[bold]Max Concurrent Tasks:[/bold] {self.config.get('system.max_concurrent_tasks')}\n"
            f"[bold]Optimization Interval:[/bold] {self.config.get('optimization.analysis_interval_seconds')}s",
            "Permanent Evolution Agent",
            "green"
        )

    def _main_loop(self):
        """主循环 - 执行与优化双并行运转，永久循环不停歇。"""
        while self._is_running and not self._shutdown_requested:
            try:
                cycle_start = time.time()
                self._execute_cycle()
                self._optimization_cycle()
                self._update_statistics(cycle_start)
                self._notify_status()
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, self._cycle_interval - cycle_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except Exception as e:
                self.log.error(f"Main loop error: {e}")
                self._handle_main_loop_error(e)
                time.sleep(1)

    def _execute_cycle(self):
        """执行周期 - 提交并监控任务执行。"""
        if not self.execution_engine:
            return
        summary = self.execution_engine.get_execution_summary()
        pending = summary.get("pending_tasks", 0)
        running = summary.get("running_tasks", 0)
        if pending < 3 and running < 5:
            task_type = ["compute", "process", "analyze"][int(time.time()) % 3]
            self.execution_engine.submit_task(
                task_type=task_type,
                payload={"index": self._statistics.total_cycles, "timestamp": time.time()}
            )

    def _optimization_cycle(self):
        """优化周期 - 持续分析执行数据，生成优化方案。"""
        if not self.data_collector or not self.optimizer_module:
            return
        if self.data_collector.has_sufficient_data():
            effectiveness = self.optimizer_module.get_optimization_effectiveness()
            if effectiveness.get("total_optimizations", 0) % 10 == 0 and effectiveness.get("total_optimizations", 0) > 0:
                self._log_optimization_progress(effectiveness)

    def _log_optimization_progress(self, effectiveness: Dict[str, Any]):
        """记录优化进度。"""
        self.log.log_optimization(
            "effectiveness_check",
            effectiveness.get("effectiveness_score", 0),
            f"Total: {effectiveness.get('total_optimizations', 0)}, "
            f"Avg Improvement: {effectiveness.get('avg_actual_improvement', 0):.2%}"
        )

    def _update_statistics(self, cycle_start: float):
        """更新统计信息。"""
        self._statistics.total_cycles += 1
        self._statistics.last_cycle_time = time.time() - cycle_start
        self._statistics.total_tasks_completed = self.config.get_metadata().get("total_tasks_completed", 0)
        self._statistics.total_optimizations = self.config.get_metadata().get("total_optimizations", 0)
        
        if self._statistics.avg_cycle_duration == 0:
            self._statistics.avg_cycle_duration = self._statistics.last_cycle_time
        else:
            alpha = 0.1
            self._statistics.avg_cycle_duration = (
                alpha * self._statistics.last_cycle_time +
                (1 - alpha) * self._statistics.avg_cycle_duration
            )

    def _notify_status(self):
        """通知状态更新。"""
        status = self.get_system_status()
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.log.error(f"Status callback error: {e}")

    def _handle_main_loop_error(self, error: Exception):
        """处理主循环错误 - 局部异常不影响整体运转。"""
        self.log.error(f"Main loop error handled: {error}")
        if self.guardian_service:
            self.guardian_service._emit_event("main_loop_error", str(error), "critical")

    def stop(self):
        """停止主循环。"""
        self.log.section_divider("Shutting Down Permanent Evolution Agent")
        self._is_running = False
        
        if self._main_loop_thread:
            self._main_loop_thread.join(timeout=5)
        
        if self.sync_layer:
            self.sync_layer.shutdown()
        
        if self.optimizer_module:
            self.optimizer_module.stop_optimization_loop()
        
        if self.execution_engine:
            self.execution_engine.shutdown()
        
        if self.guardian_service:
            self.guardian_service.stop_guardian_loop()
        
        if self.data_collector:
            self.data_collector.stop_collection()
        
        self._display_shutdown_summary()
        self.log.success("Permanent Evolution Agent stopped gracefully")

    def _display_shutdown_summary(self):
        """显示关闭摘要。"""
        uptime = time.time() - self._statistics.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        self.log.display_panel(
            f"[bold]Total Cycles:[/bold] {self._statistics.total_cycles}\n"
            f"[bold]Tasks Completed:[/bold] {self._statistics.total_tasks_completed}\n"
            f"[bold]Optimizations Applied:[/bold] {self._statistics.total_optimizations}\n"
            f"[bold]Uptime:[/bold] {hours}h {minutes}m {seconds}s\n"
            f"[bold]Avg Cycle Duration:[/bold] {self._statistics.avg_cycle_duration*1000:.2f}ms",
            "Shutdown Summary",
            "cyan"
        )

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统整体状态。"""
        status = {
            "running": self._is_running,
            "uptime": time.time() - self._statistics.start_time,
            "statistics": {
                "total_cycles": self._statistics.total_cycles,
                "total_tasks": self._statistics.total_tasks_completed,
                "total_optimizations": self._statistics.total_optimizations,
                "avg_cycle_ms": round(self._statistics.avg_cycle_duration * 1000, 2)
            }
        }
        
        if self.guardian_service:
            status["guardian"] = self.guardian_service.get_system_health_summary()
        
        if self.execution_engine:
            status["execution"] = self.execution_engine.get_execution_summary()
            if hasattr(self.execution_engine, 'get_detailed_statistics'):
                status["execution_detailed"] = self.execution_engine.get_detailed_statistics()
        
        if self.optimizer_module:
            status["optimization"] = self.optimizer_module.get_optimization_summary()
        
        if self.sync_layer:
            status["sync"] = self.sync_layer.get_sync_statistics()
        
        if self.data_collector:
            status["system_health"] = self.data_collector.get_system_health()
        
        return status

    def display_status(self):
        """显示系统状态。"""
        status = self.get_system_status()
        self.log.section_divider("System Status")
        
        health = status.get("guardian", {})
        if health:
            self.log.header(f"Guardian Health: {health.get('overall_status', 'unknown')}", "bold green" if health.get('overall_status') == 'healthy' else "bold yellow")
        
        exec_summary = status.get("execution", {})
        if exec_summary:
            self.log.header(f"Execution: {exec_summary.get('running_tasks', 0)} running, {exec_summary.get('completed_tasks', 0)} completed")
        
        opt_summary = status.get("optimization", {})
        if opt_summary:
            effectiveness = opt_summary.get("effectiveness", {})
            self.log.header(f"Optimization: {opt_summary.get('active_rules', 0)} active, {effectiveness.get('effectiveness_score', 0):.1%} effectiveness")
        
        sync_stats = status.get("sync", {})
        if sync_stats:
            self.log.header(f"Sync: {sync_stats.get('total_synced', 0)} synced, {sync_stats.get('pending_rules', 0)} pending")

    def add_status_callback(self, callback: Callable):
        """添加状态回调。"""
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable):
        """移除状态回调。"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def submit_task(self, task_type: str, payload: Any, priority: str = "NORMAL") -> str:
        """提交任务。"""
        if not self.execution_engine:
            raise RuntimeError("Execution engine not initialized")
        from task_execution_engine_core_module import TaskPriority
        return self.execution_engine.submit_task(
            task_type=task_type,
            payload=payload,
            priority=TaskPriority[priority]
        )

    def submit_batch_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """批量提交任务。"""
        if not self.execution_engine:
            raise RuntimeError("Execution engine not initialized")
        return self.execution_engine.submit_batch(tasks)

    def force_optimization(self, optimization_type: str, target: str, value: Any) -> bool:
        """强制执行优化。"""
        if not self.optimizer_module or not self.sync_layer:
            return False
        from intelligent_optimizer_module_system_layer import OptimizationType
        opt_type = OptimizationType[optimization_type.upper()]
        success = self.optimizer_module.force_optimization(opt_type, target, value)
        if success:
            rule = self.optimizer_module._optimization_rules.get(f"{optimization_type}_{target}")
            if rule:
                self.sync_layer.push_optimization(rule)
        return success

    def get_full_report(self) -> Dict[str, Any]:
        """获取完整系统报告。"""
        return {
            "system_status": self.get_system_status(),
            "execution_data": self.data_collector.get_full_analysis() if self.data_collector else {},
            "optimization_effectiveness": self.optimizer_module.get_optimization_effectiveness() if self.optimizer_module else {},
            "guardian_events": self.guardian_service.get_guardian_events(limit=20) if self.guardian_service else [],
            "config_export": self.config.export_config(),
            "loop_statistics": {
                "total_cycles": self._statistics.total_cycles,
                "avg_cycle_duration": self._statistics.avg_cycle_duration,
                "total_runtime": time.time() - self._statistics.start_time
            }
        }

    def is_running(self) -> bool:
        """检查是否正在运行。"""
        return self._is_running

    def wait(self):
        """等待主循环结束。"""
        if self._main_loop_thread:
            self._main_loop_thread.join()
