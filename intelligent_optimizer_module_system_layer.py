"""
Intelligent Optimizer Module
智能优化层 - 实时复盘执行数据，找短板、改流程、提效率、降损耗。
分析执行数据，识别瓶颈，生成优化方案，持续改进执行策略。
"""
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from shared_config_manager_core_system import SharedConfigManager
from enhanced_logging_system_utility_module import EnhancedLoggingUtility
from execution_data_collector_system_module import ExecutionDataCollector


class OptimizationType(Enum):
    SEQUENCE = "sequence"
    PARALLEL = "parallel"
    BYPASS = "bypass"
    CACHE = "cache"
    BATCH = "batch"
    TIMEOUT = "timeout"
    RETRY = "retry"
    RESOURCE = "resource"


@dataclass
class OptimizationRule:
    rule_id: str
    optimization_type: OptimizationType
    target_component: str
    description: str
    old_value: Any
    new_value: Any
    expected_improvement: float
    actual_improvement: Optional[float] = None
    applied: bool = False
    timestamp: float = field(default_factory=time.time)
    success_count: int = 0
    failure_count: int = 0


class IntelligentOptimizerModule:
    """智能优化模块 - 实时分析数据，生成并应用优化规则。"""

    def __init__(self, data_collector: ExecutionDataCollector):
        self.config = SharedConfigManager()
        self.log = EnhancedLoggingUtility()
        self.data_collector = data_collector
        self._optimization_rules: Dict[str, OptimizationRule] = {}
        self._optimization_history: List[OptimizationRule] = []
        self._is_optimizing = False
        self._optimization_thread: Optional[threading.Thread] = None
        self._optimization_lock = threading.Lock()
        self._optimization_callbacks: List[Callable] = []
        self._analysis_interval = self.config.get("optimization.analysis_interval_seconds", 10)
        self._min_samples = self.config.get("optimization.min_samples_for_analysis", 5)
        self._improvement_threshold = self.config.get("optimization.improvement_threshold", 0.05)
        self._max_rules = self.config.get("optimization.max_optimization_rules", 100)
        self._optimization_count = 0
        self._trend_window = 20

    def start_optimization_loop(self):
        """启动优化循环。"""
        if self._is_optimizing:
            return
        self._is_optimizing = True
        self._optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self._optimization_thread.start()
        self.log.log_guardian_event("start", "Intelligent optimization loop started")

    def stop_optimization_loop(self):
        """停止优化循环。"""
        self._is_optimizing = False
        if self._optimization_thread:
            self._optimization_thread.join(timeout=5)
        self.log.info("Optimization loop stopped")

    def _optimization_loop(self):
        """主优化循环 - 持续分析并生成优化方案。"""
        while self._is_optimizing:
            try:
                if self.data_collector.has_sufficient_data():
                    self._run_optimization_cycle()
                time.sleep(self._analysis_interval)
            except Exception as e:
                self.log.error(f"Optimization loop error: {e}")
                time.sleep(5)

    def _run_optimization_cycle(self):
        """执行单个优化周期。"""
        analysis = self.data_collector.get_full_analysis()
        optimizations = self._analyze_and_generate_optimizations(analysis)
        for optimization in optimizations:
            if self._should_apply_optimization(optimization):
                self._apply_optimization(optimization)
        self._cleanup_old_rules()

    def _analyze_and_generate_optimizations(self, analysis: Dict[str, Any]) -> List[OptimizationRule]:
        """分析数据并生成优化方案。"""
        optimizations = []
        optimizations.extend(self._analyze_sequence_optimizations(analysis))
        optimizations.extend(self._analyze_resource_optimizations(analysis))
        optimizations.extend(self._analyze_batch_optimizations(analysis))
        optimizations.extend(self._analyze_timeout_optimizations(analysis))
        return optimizations

    def _analyze_sequence_optimizations(self, analysis: Dict[str, Any]) -> List[OptimizationRule]:
        """分析执行序列优化机会。"""
        optimizations = []
        bottleneck_analysis = analysis.get("bottleneck_analysis", {})
        bottlenecks = bottleneck_analysis.get("bottlenecks", [])
        for bottleneck in bottlenecks:
            if bottleneck.get("severity") == "high":
                step = bottleneck.get("step", "")
                current_sequence = self.config.get_execution_rules()
                if "validate" in current_sequence and bottleneck.get("percentage", 0) > 50:
                    new_sequence = [s for s in current_sequence if s != "validate"]
                    optimization = OptimizationRule(
                        rule_id=f"seq_opt_{self._optimization_count}",
                        optimization_type=OptimizationType.BYPASS,
                        target_component="execution_sequence",
                        description=f"Bypass {step} for optimization",
                        old_value=current_sequence,
                        new_value=new_sequence,
                        expected_improvement=0.15
                    )
                    optimizations.append(optimization)
        step_analysis = analysis.get("step_analysis", {})
        for step, stats in step_analysis.items():
            if stats.get("avg", 0) > 1.0:
                optimization = OptimizationRule(
                    rule_id=f"cache_opt_{self._optimization_count}",
                    optimization_type=OptimizationType.CACHE,
                    target_component=step,
                    description=f"Add caching for {step}",
                    old_value={"cached": False},
                    new_value={"cached": True, "ttl": 300},
                    expected_improvement=0.25
                )
                optimizations.append(optimization)
        return optimizations

    def _analyze_resource_optimizations(self, analysis: Dict[str, Any]) -> List[OptimizationRule]:
        """分析资源使用优化机会。"""
        optimizations = []
        system_health = analysis.get("system_health", {})
        if system_health.get("status") == "warning":
            current_workers = self.config.get("system.max_concurrent_tasks", 10)
            if current_workers > 5:
                new_workers = max(3, int(current_workers * 0.7))
                optimization = OptimizationRule(
                    rule_id=f"resource_opt_{self._optimization_count}",
                    optimization_type=OptimizationType.RESOURCE,
                    target_component="max_concurrent_tasks",
                    description="Reduce workers under high load",
                    old_value=current_workers,
                    new_value=new_workers,
                    expected_improvement=0.10
                )
                optimizations.append(optimization)
        error_analysis = analysis.get("error_analysis", {})
        if error_analysis.get("error_rate", 0) > 0.1:
            current_retries = self.config.get("execution.retry_attempts", 3)
            if current_retries < 5:
                optimization = OptimizationRule(
                    rule_id=f"retry_opt_{self._optimization_count}",
                    optimization_type=OptimizationType.RETRY,
                    target_component="retry_attempts",
                    description="Increase retry attempts for high error rate",
                    old_value=current_retries,
                    new_value=current_retries + 1,
                    expected_improvement=0.20
                )
                optimizations.append(optimization)
        return optimizations

    def _analyze_batch_optimizations(self, analysis: Dict[str, Any]) -> List[OptimizationRule]:
        """分析批处理优化机会。"""
        optimizations = []
        metrics_summary = analysis.get("metrics_summary", {})
        avg_duration = metrics_summary.get("avg_duration", 0)
        if avg_duration > 0.5:
            current_batch = self.config.get("execution.batch_size", 5)
            if current_batch < 20:
                new_batch = min(20, int(current_batch * 1.5))
                optimization = OptimizationRule(
                    rule_id=f"batch_opt_{self._optimization_count}",
                    optimization_type=OptimizationType.BATCH,
                    target_component="batch_size",
                    description="Increase batch size for better throughput",
                    old_value=current_batch,
                    new_value=new_batch,
                    expected_improvement=0.18
                )
                optimizations.append(optimization)
        return optimizations

    def _analyze_timeout_optimizations(self, analysis: Dict[str, Any]) -> List[OptimizationRule]:
        """分析超时优化机会。"""
        optimizations = []
        step_analysis = analysis.get("step_analysis", {})
        max_duration = max((stats.get("max", 0) for stats in step_analysis.values()), default=0)
        if max_duration > 0:
            current_timeout = self.config.get("system.task_timeout_seconds", 300)
            if max_duration > current_timeout * 0.8:
                new_timeout = int(max_duration * 1.5)
                optimization = OptimizationRule(
                    rule_id=f"timeout_opt_{self._optimization_count}",
                    optimization_type=OptimizationType.TIMEOUT,
                    target_component="task_timeout",
                    description="Increase timeout for long-running tasks",
                    old_value=current_timeout,
                    new_value=new_timeout,
                    expected_improvement=0.05
                )
                optimizations.append(optimization)
        return optimizations

    def _should_apply_optimization(self, optimization: OptimizationRule) -> bool:
        """判断是否应该应用优化。"""
        if len(self._optimization_rules) >= self._max_rules:
            return False
        rule_key = f"{optimization.optimization_type.value}_{optimization.target_component}"
        if rule_key in self._optimization_rules:
            existing = self._optimization_rules[rule_key]
            if existing.applied and existing.actual_improvement is not None:
                return False
        return optimization.expected_improvement >= self._improvement_threshold

    def _apply_optimization(self, optimization: OptimizationRule):
        """应用优化规则。"""
        with self._optimization_lock:
            self._optimization_count += 1
            rule_key = f"{optimization.optimization_type.value}_{optimization.target_component}"
            optimization.rule_id = f"{optimization.rule_id}_{self._optimization_count}"
            self._optimization_rules[rule_key] = optimization
            self._optimization_history.append(optimization)
            optimization.applied = True
        if optimization.optimization_type == OptimizationType.SEQUENCE:
            self.config.update_rule("execution_sequence", optimization.new_value)
        elif optimization.optimization_type == OptimizationType.BATCH:
            self.config.set("execution.batch_size", optimization.new_value)
        elif optimization.optimization_type == OptimizationType.RESOURCE:
            self.config.set("system.max_concurrent_tasks", optimization.new_value)
        elif optimization.optimization_type == OptimizationType.TIMEOUT:
            self.config.set("system.task_timeout_seconds", optimization.new_value)
        elif optimization.optimization_type == OptimizationType.RETRY:
            self.config.set("execution.retry_attempts", optimization.new_value)
        self.log.log_optimization(
            optimization.optimization_type.value,
            optimization.expected_improvement,
            optimization.description
        )
        self._notify_optimization_applied(optimization)
        self.config.increment_stat("total_optimizations")

    def _notify_optimization_applied(self, optimization: OptimizationRule):
        """通知优化已应用。"""
        for callback in self._optimization_callbacks:
            try:
                callback(optimization)
            except Exception as e:
                self.log.error(f"Optimization callback error: {e}")

    def _cleanup_old_rules(self):
        """清理旧的优化规则。"""
        with self._optimization_lock:
            if len(self._optimization_rules) > self._max_rules:
                sorted_rules = sorted(
                    self._optimization_rules.items(),
                    key=lambda x: x[1].timestamp
                )
                to_remove = sorted_rules[:len(self._optimization_rules) - self._max_rules]
                for key, _ in to_remove:
                    del self._optimization_rules[key]

    def record_optimization_result(self, rule_id: str, success: bool, actual_improvement: Optional[float] = None):
        """记录优化结果。"""
        with self._optimization_lock:
            for rule in self._optimization_rules.values():
                if rule.rule_id == rule_id:
                    rule.actual_improvement = actual_improvement
                    if success:
                        rule.success_count += 1
                    else:
                        rule.failure_count += 1
                    break

    def get_applied_optimizations(self) -> List[Dict[str, Any]]:
        """获取已应用的优化列表。"""
        with self._optimization_lock:
            return [
                {
                    "rule_id": r.rule_id,
                    "type": r.optimization_type.value,
                    "target": r.target_component,
                    "description": r.description,
                    "expected": r.expected_improvement,
                    "actual": r.actual_improvement,
                    "applied_at": r.timestamp,
                    "success_rate": r.success_count / (r.success_count + r.failure_count)
                    if (r.success_count + r.failure_count) > 0 else None
                }
                for r in self._optimization_rules.values()
            ]

    def get_optimization_effectiveness(self) -> Dict[str, Any]:
        """获取优化有效性统计。"""
        with self._optimization_lock:
            rules = list(self._optimization_rules.values())
            if not rules:
                return {"total_optimizations": 0, "avg_improvement": 0, "effectiveness_score": 0}
            improvements = [r.actual_improvement for r in rules if r.actual_improvement is not None]
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0
            total_successes = sum(r.success_count for r in rules)
            total_failures = sum(r.failure_count for r in rules)
            effectiveness = total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0
            return {
                "total_optimizations": len(rules),
                "avg_expected_improvement": sum(r.expected_improvement for r in rules) / len(rules),
                "avg_actual_improvement": avg_improvement,
                "effectiveness_score": effectiveness,
                "total_successes": total_successes,
                "total_failures": total_failures
            }

    def get_recommended_adjustments(self) -> List[Dict[str, Any]]:
        """获取建议的调整项。"""
        recommendations = []
        system_health = self.data_collector.get_system_health()
        if system_health.get("status") == "critical":
            recommendations.append({
                "type": "emergency",
                "suggestion": "System in critical state - reduce load immediately",
                "action": "reduce_concurrent_tasks"
            })
        error_analysis = self.data_collector.get_error_analysis()
        if error_analysis.get("error_rate", 0) > 0.15:
            recommendations.append({
                "type": "error_rate",
                "suggestion": "High error rate detected - review error patterns",
                "action": "investigate_errors"
            })
        return recommendations

    def add_optimization_callback(self, callback: Callable):
        """添加优化回调函数。"""
        self._optimization_callbacks.append(callback)

    def remove_optimization_callback(self, callback: Callable):
        """移除优化回调函数。"""
        if callback in self._optimization_callbacks:
            self._optimization_callbacks.remove(callback)

    def force_optimization(self, optimization_type: OptimizationType, target: str, new_value: Any) -> bool:
        """强制执行特定优化。"""
        rule = OptimizationRule(
            rule_id=f"forced_{self._optimization_count}",
            optimization_type=optimization_type,
            target_component=target,
            description=f"Forced optimization for {target}",
            old_value=self.config.get(target),
            new_value=new_value,
            expected_improvement=0.10
        )
        self._apply_optimization(rule)
        return True

    def revert_optimization(self, rule_id: str) -> bool:
        """回滚优化规则。"""
        with self._optimization_lock:
            for key, rule in self._optimization_rules.items():
                if rule.rule_id == rule_id:
                    self.config.update_rule(f"execution_sequence", rule.old_value)
                    del self._optimization_rules[key]
                    self.log.log_rule_update(f"Reverted {rule_id}", rule.new_value, rule.old_value)
                    return True
        return False

    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要。"""
        return {
            "active_rules": len(self._optimization_rules),
            "total_optimizations": self._optimization_count,
            "effectiveness": self.get_optimization_effectiveness(),
            "recommendations": self.get_recommended_adjustments(),
            "recent_optimizations": self.get_applied_optimizations()[-5:]
        }
