"""
Sync Implementation Layer
同步落地层 - 将优化规则即时同步应用到执行层，确保优化成果无缝衔接下一轮任务。
实时监控规则变化，自动推送到执行引擎，零延迟生效。
"""
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib
import json

from shared_config_manager_core_system import SharedConfigManager
from enhanced_logging_system_utility_module import EnhancedLoggingUtility


class RulePriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class SyncRule:
    rule_id: str
    rule_type: str
    target: str
    value: Any
    priority: RulePriority = RulePriority.NORMAL
    version: int = 1
    checksum: str = ""
    created_at: float = field(default_factory=time.time)
    applied_at: Optional[float] = None
    sync_status: str = "pending"


class SyncImplementationLayer:
    """同步落地层 - 规则即时生效，无缝衔接执行流程。"""

    def __init__(self):
        self.config = SharedConfigManager()
        self.log = EnhancedLoggingUtility()
        self._pending_rules: deque = deque(maxlen=500)
        self._applied_rules: Dict[str, SyncRule] = {}
        self._rule_versions: Dict[str, int] = {}
        self._sync_targets: Set[str] = set()
        self._sync_callbacks: Dict[str, Callable] = {}
        self._sync_lock = threading.Lock()
        self._is_syncing = False
        self._sync_thread: Optional[threading.Thread] = None
        self._sync_interval = 0.1
        self._max_pending_rules = 100
        self._rule_cache: Dict[str, Any] = {}
        self._sync_statistics = {
            "total_synced": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "last_sync_time": 0
        }

    def initialize(self):
        """初始化同步层。"""
        self._is_syncing = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        self._register_default_sync_targets()
        self.log.log_guardian_event("start", "Sync implementation layer initialized")

    def shutdown(self):
        """关闭同步层。"""
        self._is_syncing = False
        if self._sync_thread:
            self._sync_thread.join(timeout=3)
        self._flush_pending_rules()
        self.log.info("Sync implementation layer shutdown")

    def _register_default_sync_targets(self):
        """注册默认同步目标。"""
        self.register_sync_target("execution_sequence", self._sync_execution_sequence)
        self.register_sync_target("max_concurrent_tasks", self._sync_max_workers)
        self.register_sync_target("batch_size", self._sync_batch_size)
        self.register_sync_target("task_timeout", self._sync_timeout)
        self.register_sync_target("retry_attempts", self._sync_retry_attempts)

    def register_sync_target(self, target: str, callback: Callable[[Any], bool]):
        """注册同步目标处理器。"""
        with self._sync_lock:
            self._sync_targets.add(target)
            self._sync_callbacks[target] = callback
        self.log.debug(f"Registered sync target: {target}")

    def unregister_sync_target(self, target: str):
        """注销同步目标。"""
        with self._sync_lock:
            self._sync_targets.discard(target)
            if target in self._sync_callbacks:
                del self._sync_callbacks[target]
        self.log.debug(f"Unregistered sync target: {target}")

    def queue_rule(self, rule: SyncRule):
        """将规则加入同步队列。"""
        with self._sync_lock:
            self._pending_rules.append(rule)
            self.log.debug(f"Rule queued: {rule.rule_id} -> {rule.target}")

    def push_optimization(self, optimization: Any):
        """推送优化规则到同步队列。"""
        rule_type = getattr(optimization, 'optimization_type', None)
        target = getattr(optimization, 'target_component', 'unknown')
        new_value = getattr(optimization, 'new_value', None)
        expected_improvement = getattr(optimization, 'expected_improvement', 0)

        if rule_type:
            rule_type = rule_type.value if hasattr(rule_type, 'value') else str(rule_type)

        rule = SyncRule(
            rule_id=getattr(optimization, 'rule_id', f"opt_{time.time()}"),
            rule_type=rule_type or "general",
            target=target,
            value=new_value,
            priority=self._determine_priority(expected_improvement)
        )
        rule.checksum = self._calculate_checksum(rule)
        self.queue_rule(rule)

    def _determine_priority(self, improvement: float) -> RulePriority:
        """根据改进幅度确定优先级。"""
        if improvement >= 0.20:
            return RulePriority.CRITICAL
        elif improvement >= 0.10:
            return RulePriority.HIGH
        elif improvement >= 0.05:
            return RulePriority.NORMAL
        return RulePriority.LOW

    def _calculate_checksum(self, rule: SyncRule) -> str:
        """计算规则校验和。"""
        rule_data = f"{rule.rule_id}:{rule.target}:{json.dumps(rule.value)}"
        return hashlib.md5(rule_data.encode()).hexdigest()[:8]

    def _sync_loop(self):
        """同步循环 - 持续处理待同步规则。"""
        while self._is_syncing:
            try:
                self._process_pending_rules()
                time.sleep(self._sync_interval)
            except Exception as e:
                self.log.error(f"Sync loop error: {e}")
                time.sleep(1)

    def _process_pending_rules(self):
        """处理待同步规则。"""
        with self._sync_lock:
            rules_to_process = list(self._pending_rules)
            self._pending_rules.clear()
        rules_to_process.sort(key=lambda r: r.priority.value)
        for rule in rules_to_process:
            self._apply_rule_sync(rule)

    def _apply_rule_sync(self, rule: SyncRule) -> bool:
        """同步应用单个规则。"""
        try:
            if rule.target not in self._sync_targets:
                self._sync_statistics["total_skipped"] += 1
                return False
            if self._is_duplicate_rule(rule):
                self._sync_statistics["total_skipped"] += 1
                return False
            callback = self._sync_callbacks.get(rule.target)
            if callback:
                success = callback(rule.value)
                if success:
                    rule.sync_status = "applied"
                    rule.applied_at = time.time()
                    self._update_applied_rules(rule)
                    self._sync_statistics["total_synced"] += 1
                    self._sync_statistics["last_sync_time"] = time.time()
                    self.log.debug(f"Rule synced: {rule.rule_id} -> {rule.target}")
                    return True
                else:
                    rule.sync_status = "failed"
                    self._sync_statistics["total_failed"] += 1
            return False
        except Exception as e:
            self.log.error(f"Rule sync error for {rule.rule_id}: {e}")
            rule.sync_status = "failed"
            self._sync_statistics["total_failed"] += 1
            return False

    def _is_duplicate_rule(self, rule: SyncRule) -> bool:
        """检查是否为重复规则。"""
        existing = self._applied_rules.get(rule.target)
        if existing and existing.checksum == rule.checksum:
            return True
        return False

    def _update_applied_rules(self, rule: SyncRule):
        """更新已应用的规则。"""
        with self._sync_lock:
            rule.version = self._rule_versions.get(rule.target, 0) + 1
            self._applied_rules[rule.target] = rule
            self._rule_versions[rule.target] = rule.version
            self._rule_cache[rule.target] = rule.value

    def _flush_pending_rules(self):
        """刷新所有待处理规则。"""
        with self._sync_lock:
            rules_to_flush = list(self._pending_rules)
            self._pending_rules.clear()
        for rule in rules_to_flush:
            self._apply_rule_sync(rule)

    def _sync_execution_sequence(self, value: Any) -> bool:
        """同步执行序列。"""
        try:
            if isinstance(value, list):
                self.config.update_rule("execution_sequence", value)
                return True
            return False
        except Exception as e:
            self.log.error(f"Execution sequence sync error: {e}")
            return False

    def _sync_max_workers(self, value: Any) -> bool:
        """同步最大工作线程数。"""
        try:
            if isinstance(value, int) and value > 0:
                self.config.set("system.max_concurrent_tasks", value)
                return True
            return False
        except Exception as e:
            self.log.error(f"Max workers sync error: {e}")
            return False

    def _sync_batch_size(self, value: Any) -> bool:
        """同步批处理大小。"""
        try:
            if isinstance(value, int) and value > 0:
                self.config.set("execution.batch_size", value)
                return True
            return False
        except Exception as e:
            self.log.error(f"Batch size sync error: {e}")
            return False

    def _sync_timeout(self, value: Any) -> bool:
        """同步超时设置。"""
        try:
            if isinstance(value, (int, float)) and value > 0:
                self.config.set("system.task_timeout_seconds", value)
                return True
            return False
        except Exception as e:
            self.log.error(f"Timeout sync error: {e}")
            return False

    def _sync_retry_attempts(self, value: Any) -> bool:
        """同步重试次数。"""
        try:
            if isinstance(value, int) and value >= 0:
                self.config.set("execution.retry_attempts", value)
                return True
            return False
        except Exception as e:
            self.log.error(f"Retry attempts sync error: {e}")
            return False

    def force_sync(self, target: str, value: Any) -> bool:
        """强制同步特定目标。"""
        rule = SyncRule(
            rule_id=f"force_{time.time()}",
            rule_type="forced",
            target=target,
            value=value,
            priority=RulePriority.CRITICAL
        )
        rule.checksum = self._calculate_checksum(rule)
        return self._apply_rule_sync(rule)

    def get_sync_status(self, target: str) -> Optional[Dict[str, Any]]:
        """获取同步目标状态。"""
        with self._sync_lock:
            applied_rule = self._applied_rules.get(target)
            if applied_rule:
                return {
                    "target": target,
                    "status": applied_rule.sync_status,
                    "version": applied_rule.version,
                    "applied_at": applied_rule.applied_at,
                    "checksum": applied_rule.checksum
                }
        return None

    def get_all_sync_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有同步目标状态。"""
        with self._sync_lock:
            return {
                target: self.get_sync_status(target) or {"status": "not_synced"}
                for target in self._sync_targets
            }

    def get_pending_rules_count(self) -> int:
        """获取待处理规则数量。"""
        with self._sync_lock:
            return len(self._pending_rules)

    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计。"""
        stats = self._sync_statistics.copy()
        with self._sync_lock:
            stats["pending_rules"] = len(self._pending_rules)
            stats["applied_rules"] = len(self._applied_rules)
            stats["sync_targets"] = len(self._sync_targets)
            stats["cache_size"] = len(self._rule_cache)
        return stats

    def clear_rule_cache(self, target: Optional[str] = None):
        """清除规则缓存。"""
        with self._sync_lock:
            if target:
                self._rule_cache.pop(target, None)
            else:
                self._rule_cache.clear()
        self.log.debug(f"Rule cache cleared: {target or 'all'}")

    def get_applied_rule(self, target: str) -> Optional[SyncRule]:
        """获取已应用的规则。"""
        with self._sync_lock:
            return self._applied_rules.get(target)

    def rollback_rule(self, target: str) -> bool:
        """回滚规则到之前版本。"""
        with self._sync_lock:
            if target not in self._applied_rules:
                return False
            current_rule = self._applied_rules[target]
            if current_rule.version > 1:
                self._rule_versions[target] -= 1
                current_rule.version -= 1
                current_rule.value = self._rule_cache.get(target, current_rule.value)
                self.log.log_rule_update(f"Rule rollback: {target}", current_rule.version + 1, current_rule.version)
                return True
        return False

    def is_healthy(self) -> bool:
        """检查同步层健康状态。"""
        with self._sync_lock:
            pending_count = len(self._pending_rules)
            failed_ratio = self._sync_statistics["total_failed"] / max(1, self._sync_statistics["total_synced"])
        return pending_count < self._max_pending_rules and failed_ratio < 0.1

    def wait_for_sync(self, timeout: float = 5.0) -> bool:
        """等待所有规则同步完成。"""
        start_time = time.time()
        while self.get_pending_rules_count() > 0:
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.01)
        return True
