#!/usr/bin/env python3
"""
高级综合测试框架 - 6大测试场景持续运行
测试目标：发现竞态条件、内存泄漏、异常恢复、长时间稳定性等深层问题
"""
import sys
import time
import random
import threading
import traceback
import gc
import os
import psutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque
from dataclasses import dataclass, asdict
import hashlib

sys.path.insert(0, '/workspace')


@dataclass
class TestBug:
    """测试发现的Bug"""
    id: int
    type: str
    severity: str
    message: str
    stacktrace: str
    timestamp: float
    component: str


class AdvancedBugTracker:
    """高级Bug追踪器"""
    
    def __init__(self):
        self.bugs: List[TestBug] = []
        self.metrics: Dict[str, deque] = {
            'cpu': deque(maxlen=300),
            'memory': deque(maxlen=300),
            'gc_count': deque(maxlen=100),
            'threads': deque(maxlen=100)
        }
        self._lock = threading.Lock()
        self._bug_counts = {}
        self._unique_bugs = set()
        
    def record(self, bug_type: str, severity: str, msg: str, stacktrace: str = None, component: str = "system"):
        bug_id = len(self.bugs) + 1
        bug_hash = hashlib.md5(f"{bug_type}:{msg}".encode()).hexdigest()[:8]
        
        with self._lock:
            if bug_hash in self._unique_bugs:
                return None
            self._unique_bugs.add(bug_hash)
            
            bug = TestBug(
                id=bug_id,
                type=bug_type,
                severity=severity,
                message=msg,
                stacktrace=stacktrace or "",
                timestamp=time.time(),
                component=component
            )
            self.bugs.append(bug)
            
            if bug_type not in self._bug_counts:
                self._bug_counts[bug_type] = 0
            self._bug_counts[bug_type] += 1
            
            return bug
    
    def track(self, name: str, value: float):
        if name in self.metrics:
            self.metrics[name].append({'time': time.time(), 'value': value})


class ConcurrencyTest:
    """测试1: 竞态条件和并发安全性"""
    
    def __init__(self, agent, tracker: AdvancedBugTracker):
        self.agent = agent
        self.tracker = tracker
        self.shared_state = {'counter': 0, 'lock': threading.Lock()}
        self.errors = []
        
    def run(self):
        """运行并发测试"""
        threads = []
        for i in range(20):
            t = threading.Thread(target=self._concurrent_worker, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        expected = 200
        actual = self.shared_state['counter']
        if actual != expected:
            self.tracker.record(
                'race_condition',
                'critical',
                f'竞态条件: 期望值={expected}, 实际值={actual}',
                traceback.format_stack(),
                'concurrency'
            )
            
        if self.errors:
            for err in self.errors[:3]:
                self.tracker.record('concurrency_error', 'high', err, None, 'concurrency')
                
    def _concurrent_worker(self, worker_id: int):
        for i in range(10):
            with self.shared_state['lock']:
                old = self.shared_state['counter']
                time.sleep(0.0001)
                self.shared_state['counter'] = old + 1
                
            try:
                task_id = self.agent.submit_task('compute', {'worker': worker_id, 'iter': i})
                result = self.agent.execution_engine.get_task_result(task_id)
                if result is None and i % 5 == 0:
                    self.errors.append(f"Worker {worker_id}: result is None")
            except Exception as e:
                self.errors.append(f"Worker {worker_id}: {str(e)}")


class MemoryLeakTest:
    """测试2: 内存泄漏检测"""
    
    def __init__(self, agent, tracker: AdvancedBugTracker):
        self.agent = agent
        self.tracker = tracker
        self.initial_memory = None
        
    def run(self):
        """运行内存泄漏测试"""
        process = psutil.Process()
        
        if self.initial_memory is None:
            self.initial_memory = process.memory_info().rss / 1024 / 1024
            
        gc.collect()
        before = process.memory_info().rss / 1024 / 1024
        
        for _ in range(100):
            self.agent.submit_task('process', {'data': [{'k': f'v{i}'} for i in range(100)]})
            
        time.sleep(2)
        gc.collect()
        after = process.memory_info().rss / 1024 / 1024
        
        growth = after - before
        self.tracker.track('memory', after)
        
        if growth > 20:
            self.tracker.record(
                'memory_leak',
                'high',
                f'内存增长过多: {growth:.1f}MB (before={before:.1f}, after={after:.1f})',
                None,
                'memory'
            )
            
        total_growth = after - self.initial_memory
        if total_growth > 100:
            self.tracker.record(
                'memory_leak_cumulative',
                'critical',
                f'累积内存泄漏: {total_growth:.1f}MB',
                None,
                'memory'
            )


class ExceptionRecoveryTest:
    """测试3: 异常恢复和容错"""
    
    def __init__(self, agent, tracker: AdvancedBugTracker):
        self.agent = agent
        self.tracker = tracker
        
    def run(self):
        """运行异常恢复测试"""
        edge_cases = [
            ('compute', None),
            ('process', {}),
            ('analyze', {'nested': {'deep': None}}),
            ('compute', {'size': 'x' * 100000}),
            ('unknown', {}),
        ]
        
        for task_type, payload in edge_cases:
            try:
                task_id = self.agent.submit_task(task_type, payload)
                time.sleep(0.5)
                status = self.agent.execution_engine.get_task_status(task_id)
                if status is None:
                    self.tracker.record(
                        'task_status_missing',
                        'medium',
                        f'任务状态缺失: {task_type}',
                        None,
                        'error_handling'
                    )
            except Exception as e:
                self.tracker.record(
                    'exception_not_caught',
                    'high',
                    f'异常未被捕获: {task_type} - {str(e)}',
                    traceback.format_exc(),
                    'error_handling'
                )
        
        guardian_events = self.agent.guardian_service.get_guardian_events(limit=10)
        error_events = [e for e in guardian_events if e.get('severity') in ['critical', 'warning']]
        
        if len(error_events) > 5:
            self.tracker.record(
                'excessive_errors',
                'high',
                f'过多错误事件: {len(error_events)}',
                None,
                'guardian'
            )


class DataConsistencyTest:
    """测试4: 数据一致性"""
    
    def __init__(self, agent, tracker: AdvancedBugTracker):
        self.agent = agent
        self.tracker = tracker
        
    def run(self):
        """运行数据一致性测试"""
        task_ids = []
        for i in range(20):
            tid = self.agent.submit_task('compute', {'index': i, 'data': f'test_{i}'})
            task_ids.append(tid)
            
        time.sleep(3)
        
        results = {}
        for tid in task_ids:
            result = self.agent.execution_engine.get_task_result(tid)
            results[tid] = result
            
        none_results = [tid for tid, r in results.items() if r is None]
        if none_results:
            self.tracker.record(
                'inconsistent_results',
                'medium',
                f'任务结果不一致: {len(none_results)}个结果为None',
                None,
                'consistency'
            )
            
        try:
            config1 = self.agent.config.get('system.max_concurrent_tasks')
            config2 = self.agent.execution_engine._max_workers
            if config1 != config2:
                self.tracker.record(
                    'config_inconsistency',
                    'medium',
                    f'配置不一致: config={config1}, engine={config2}',
                    None,
                    'consistency'
                )
        except Exception as e:
            self.tracker.record('config_error', 'high', str(e), traceback.format_exc(), 'consistency')


class PerformanceDegradationTest:
    """测试5: 性能退化检测"""
    
    def __init__(self, agent, tracker: AdvancedBugTracker):
        self.agent = agent
        self.tracker = tracker
        self.start_time = time.time()
        self.latencies = []
        
    def run(self):
        """运行性能退化测试"""
        latencies = []
        for i in range(50):
            start = time.time()
            self.agent.submit_task('compute', {'index': i})
            latency = time.time() - start
            latencies.append(latency)
            
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        self.tracker.track('latency', avg_latency * 1000)
        
        if avg_latency > 0.1:
            self.tracker.record(
                'slow_performance',
                'medium',
                f'平均延迟过高: {avg_latency*1000:.1f}ms',
                None,
                'performance'
            )
            
        if max_latency > 1.0:
            self.tracker.record(
                'latency_spike',
                'high',
                f'延迟峰值: {max_latency*1000:.1f}ms',
                None,
                'performance'
            )


class LongTermStabilityTest:
    """测试6: 长时间稳定性"""
    
    def __init__(self, agent, tracker: AdvancedBugTracker):
        self.agent = agent
        self.tracker = tracker
        self.hourly_metrics = deque(maxlen=24)
        
    def run(self, duration_seconds: int = 300):
        """运行长时间稳定性测试"""
        start = time.time()
        task_count_start = self.agent.config.get_metadata().get('total_tasks_completed', 0)
        
        while time.time() - start < duration_seconds:
            gc.collect()
            process = psutil.Process()
            
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / 1024 / 1024
            threads = process.num_threads()
            
            self.tracker.track('cpu', cpu)
            self.tracker.track('memory', memory)
            self.tracker.track('threads', threads)
            
            current_tasks = self.agent.config.get_metadata().get('total_tasks_completed', 0)
            throughput = (current_tasks - task_count_start) / (time.time() - start) if time.time() > start else 0
            
            if cpu > 95:
                self.tracker.record('high_cpu', 'medium', f'持续高CPU: {cpu:.1f}%', None, 'stability')
                
            if threads > 50:
                self.tracker.record('thread_leak', 'high', f'线程数过多: {threads}', None, 'stability')
                
            time.sleep(10)
            
        status = self.agent.get_system_status()
        if status['guardian']['overall_status'] != 'healthy':
            self.tracker.record(
                'unhealthy_state',
                'critical',
                f'系统不健康: {status["guardian"]["overall_status"]}',
                None,
                'stability'
            )


def run_advanced_tests():
    """运行高级综合测试"""
    print("=" * 80)
    print("🚀 高级综合测试框架 - 6大测试场景")
    print("=" * 80)
    
    tracker = AdvancedBugTracker()
    
    from main_loop_controller_orchestrator_system import MainLoopController
    
    print("\n📦 初始化Agent...")
    agent = MainLoopController()
    agent.initialize()
    agent.start()
    
    time.sleep(5)
    
    tests = [
        ConcurrencyTest(agent, tracker),
        MemoryLeakTest(agent, tracker),
        ExceptionRecoveryTest(agent, tracker),
        DataConsistencyTest(agent, tracker),
        PerformanceDegradationTest(agent, tracker),
        LongTermStabilityTest(agent, tracker),
    ]
    
    test_names = [
        "竞态条件和并发安全性",
        "内存泄漏检测",
        "异常恢复和容错",
        "数据一致性",
        "性能退化检测",
        "长时间稳定性测试"
    ]
    
    monitor = threading.Thread(target=monitor_system, args=(agent, tracker), daemon=True)
    monitor.start()
    
    print("\n🧪 开始运行测试...")
    
    for i, (test, name) in enumerate(zip(tests, test_names)):
        print(f"\n{'='*60}")
        print(f"📋 测试 {i+1}/6: {name}")
        print(f"{'='*60}")
        
        try:
            test.run()
        except Exception as e:
            tracker.record('test_error', 'critical', f'{name} failed: {str(e)}', traceback.format_exc(), 'testing')
            
        time.sleep(2)
        
    generate_report(tracker, agent)
    
    agent.stop()


def monitor_system(agent, tracker):
    """系统监控"""
    while True:
        try:
            process = psutil.Process()
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / 1024 / 1024
            threads = process.num_threads()
            
            tracker.track('cpu', cpu)
            tracker.track('memory', memory)
            tracker.track('threads', threads)
            tracker.track('gc_count', len(gc.get_stats()))
            
            time.sleep(2)
        except:
            pass


def generate_report(tracker: AdvancedBugTracker, agent):
    """生成测试报告"""
    print("\n" + "=" * 80)
    print("📋 高级综合测试报告")
    print("=" * 80)
    
    print(f"\n⏱️  测试时间: {datetime.now().isoformat()}")
    print(f"🔴 发现Bug总数: {len(tracker.bugs)}")
    
    bug_types = {}
    for bug in tracker.bugs:
        if bug.type not in bug_types:
            bug_types[bug.type] = []
        bug_types[bug.type].append(bug)
        
    print(f"\n📊 Bug类型分布:")
    for t, bugs in sorted(bug_types.items(), key=lambda x: len(x[1]), reverse=True):
        critical = sum(1 for b in bugs if b.severity == 'critical')
        high = sum(1 for b in bugs if b.severity == 'high')
        medium = sum(1 for b in bugs if b.severity == 'medium')
        print(f"   {t}: {len(bugs)} (critical={critical}, high={high}, medium={medium})")
        
    if tracker.metrics['cpu']:
        avg_cpu = sum(m['value'] for m in tracker.metrics['cpu']) / len(tracker.metrics['cpu'])
        max_cpu = max(m['value'] for m in tracker.metrics['cpu'])
        print(f"\n💻 CPU统计:")
        print(f"   平均: {avg_cpu:.1f}%")
        print(f"   最大: {max_cpu:.1f}%")
        
    if tracker.metrics['memory']:
        avg_mem = sum(m['value'] for m in tracker.metrics['memory']) / len(tracker.metrics['memory'])
        max_mem = max(m['value'] for m in tracker.metrics['memory'])
        print(f"\n💾 内存统计:")
        print(f"   平均: {avg_mem:.1f}MB")
        print(f"   最大: {max_mem:.1f}MB")
        
    if tracker.metrics['threads']:
        avg_threads = sum(m['value'] for m in tracker.metrics['threads']) / len(tracker.metrics['threads'])
        max_threads = max(m['value'] for m in tracker.metrics['threads'])
        print(f"\n🔢 线程统计:")
        print(f"   平均: {avg_threads:.1f}")
        print(f"   最大: {max_threads:.0f}")
        
    status = agent.get_system_status()
    print(f"\n🏥 系统状态:")
    print(f"   Guardian: {status['guardian']['overall_status']}")
    print(f"   完成任务: {status['statistics']['total_tasks']}")
    print(f"   健康组件: {status['guardian']['healthy_count']}/{status['guardian']['total_components']}")
    
    if tracker.bugs:
        print(f"\n🔴 严重Bug详情:")
        critical_bugs = [b for b in tracker.bugs if b.severity == 'critical']
        for bug in critical_bugs:
            print(f"\n   #{bug.id} [{bug.component}] {bug.type}")
            print(f"   {bug.message}")
            if bug.stacktrace:
                print(f"   Stack: {bug.stacktrace[:200]}")
                
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    run_advanced_tests()
