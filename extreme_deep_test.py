#!/usr/bin/env python3
"""
极深度压力测试框架 - 极限性能验证
包括：极端并发、长时间稳定性、内存泄漏深度检测、性能瓶颈分析
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
import heapq
import struct
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from collections import deque, defaultdict
from dataclasses import dataclass
import multiprocessing

sys.path.insert(0, '/workspace')


@dataclass
class DeepBug:
    """深度Bug记录"""
    id: int
    type: str
    severity: str
    message: str
    details: Dict[str, Any]
    stacktrace: str
    timestamp: float
    component: str
    system_load: float


class DeepTestTracker:
    """深度测试追踪器"""
    
    def __init__(self):
        self.bugs: List[DeepBug] = []
        self.metrics_history: defaultdict = defaultdict(deque)
        self._lock = threading.Lock()
        self._unique_bugs = set()
        self.start_time = time.time()
        
    def record_bug(self, bug_type: str, severity: str, msg: str, 
                   details: Dict[str, Any] = None, component: str = "system"):
        bug_id = len(self.bugs) + 1
        bug_hash = hashlib.md5(f"{bug_type}:{msg}".encode()).hexdigest()[:12]
        
        with self._lock:
            if bug_hash in self._unique_bugs:
                return None
            self._unique_bugs.add(bug_hash)
            
            process = psutil.Process()
            bug = DeepBug(
                id=bug_id,
                type=bug_type,
                severity=severity,
                message=msg,
                details=details or {},
                stacktrace=traceback.format_exc(),
                timestamp=time.time(),
                component=component,
                system_load=process.cpu_percent(interval=0.1)
            )
            self.bugs.append(bug)
            
            return bug
    
    def track_metric(self, name: str, value: float):
        with self._lock:
            self.metrics_history[name].append({
                'time': time.time(),
                'value': value
            })
            if len(self.metrics_history[name]) > 1000:
                self.metrics_history[name].popleft()


class ExtremeConcurrencyTest:
    """测试1: 极端并发压力 - 100+ 线程"""
    
    def __init__(self, agent, tracker: DeepTestTracker):
        self.agent = agent
        self.tracker = tracker
        self.results = []
        self.exceptions = []
        
    def run(self):
        print(f"\n{'='*60}")
        print(f"🧪 极端并发压力测试 - 100+线程")
        print(f"{'='*60}")
        
        for thread_count in [10, 20, 50, 100]:
            self._test_concurrency_level(thread_count)
            
        print(f"\n   完成！发现异常: {len(self.exceptions)}个")
        
        if self.exceptions:
            for exc in self.exceptions[:5]:
                self.tracker.record_bug('extreme_concurrency_error', 'critical', 
                                        str(exc), component='extreme_concurrency')
                
    def _test_concurrency_level(self, n_threads: int):
        print(f"\n   ▶️  测试 {n_threads} 个并发线程...")
        start = time.time()
        threads = []
        tasks_completed = [0]
        
        for i in range(n_threads):
            t = threading.Thread(target=self._worker_thread, 
                                args=(i, n_threads, tasks_completed))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        elapsed = time.time() - start
        total_tasks = tasks_completed[0]
        throughput = total_tasks / elapsed if elapsed > 0 else 0
        
        print(f"   ✅ {n_threads}线程: {total_tasks}任务, {throughput:.1f}任务/秒, {elapsed:.1f}秒")
        
        if throughput < 50:
            self.tracker.record_bug('performance_degradation', 'high', 
                                    f'吞吐量过低: {throughput:.1f}任务/秒 (线程数={n_threads})',
                                    component='extreme_concurrency')
            
    def _worker_thread(self, worker_id: int, total_workers: int, tasks_completed: list):
        for i in range(20):
            try:
                task_id = self.agent.submit_task('compute', {
                    'worker': worker_id, 'total': total_workers, 'iter': i
                })
                time.sleep(0.001)
                tasks_completed[0] += 1
            except Exception as e:
                self.exceptions.append(e)


class LongTermLeakTest:
    """测试2: 长时间内存泄漏检测 - 30分钟"""
    
    def __init__(self, agent, tracker: DeepTestTracker):
        self.agent = agent
        self.tracker = tracker
        self.running = False
        
    def run(self, duration_minutes: int = 10):
        print(f"\n{'='*60}")
        print(f"💾 长时间内存泄漏检测 - {duration_minutes}分钟")
        print(f"{'='*60}")
        
        process = psutil.Process()
        self.running = True
        
        monitor_thread = threading.Thread(target=self._monitor_memory, args=(process, duration_minutes), daemon=True)
        monitor_thread.start()
        
        start = time.time()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        last_memory = baseline_memory
        
        while time.time() - start < duration_minutes * 60:
            elapsed = time.time() - start
            
            for _ in range(50):
                self.agent.submit_task('process', {
                    'data': [{'id': i, 'val': random.randint(0, 1000000)} for i in range(100)]
                })
                
            gc.collect()
            current_memory = process.memory_info().rss / 1024 / 1024
            self.tracker.track_metric('memory_mb', current_memory)
            
            growth = current_memory - baseline_memory
            
            if growth > 50:
                self.tracker.record_bug('memory_leak_critical', 'critical', 
                                        f'内存泄漏严重: 增长{growth:.1f}MB (从{baseline_memory:.1f}到{current_memory:.1f}MB)',
                                        component='memory_leak')
                
            if elapsed % 60 < 1:
                mins = int(elapsed / 60)
                print(f"   📊 第{mins}分钟: {current_memory:.1f}MB (增长+{growth:.1f}MB)")
                
            time.sleep(1)
            
        self.running = False
        monitor_thread.join()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory
        print(f"\n   📊 最终: {final_memory:.1f}MB, 总增长: +{total_growth:.1f}MB")
        
        if total_growth > 30:
            self.tracker.record_bug('memory_leak', 'high', 
                                    f'累积内存增长: {total_growth:.1f}MB',
                                    component='memory_leak')
            
    def _monitor_memory(self, process, duration_minutes):
        start = time.time()
        while self.running and time.time() - start < duration_minutes * 60:
            self.tracker.track_metric('memory_mb', process.memory_info().rss / 1024 / 1024)
            self.tracker.track_metric('cpu_percent', process.cpu_percent(interval=0.1))
            time.sleep(2)


class PerformanceBottleneckTest:
    """测试3: 性能瓶颈深度分析"""
    
    def __init__(self, agent, tracker: DeepTestTracker):
        self.agent = agent
        self.tracker = tracker
        
    def run(self):
        print(f"\n{'='*60}")
        print(f"⚡ 性能瓶颈深度分析")
        print(f"{'='*60}")
        
        benchmarks = [
            ('task_submit', self._benchmark_task_submit),
            ('data_collection', self._benchmark_data_collection),
            ('guardian_monitor', self._benchmark_guardian_monitor),
            ('optimizer', self._benchmark_optimizer),
        ]
        
        for name, func in benchmarks:
            try:
                result = func()
                print(f"   🔹 {name}: {result}")
            except Exception as e:
                self.tracker.record_bug('benchmark_error', 'medium', 
                                        f'基准测试失败: {name}', component='bottleneck')
                
    def _benchmark_task_submit(self) -> Dict:
        latencies = []
        for i in range(100):
            start = time.time()
            self.agent.submit_task('compute', {'i': i})
            latencies.append(time.time() - start)
            
        avg_latency = sum(latencies) / len(latencies) * 1000
        p99_latency = heapq.nlargest(1, latencies)[0] * 1000
        self.tracker.track_metric('submit_latency_ms', avg_latency)
        
        return {'avg_ms': avg_latency, 'p99_ms': p99_latency}
        
    def _benchmark_data_collection(self) -> Dict:
        collector = self.agent.data_collector
        start = time.time()
        for i in range(50):
            collector.collect_execution_metric(f'test_task_{i}', 0.1, 'success')
        latency = (time.time() - start) / 50 * 1000
        
        return {'avg_metric_latency_ms': latency}
        
    def _benchmark_guardian_monitor(self) -> Dict:
        guardian = self.agent.guardian_service
        start = time.time()
        status = guardian.get_system_status()
        latency = (time.time() - start) * 1000
        
        return {'status_check_latency_ms': latency, 'status': status['overall_status']}
        
    def _benchmark_optimizer(self) -> Dict:
        optimizer = self.agent.intelligent_optimizer
        start = time.time()
        insights = optimizer.generate_optimization_insights()
        latency = (time.time() - start) * 1000
        
        return {'optimize_latency_ms': latency, 'insights_count': len(insights)}


class StressRecoveryTest:
    """测试4: 压力后的恢复能力"""
    
    def __init__(self, agent, tracker: DeepTestTracker):
        self.agent = agent
        self.tracker = tracker
        
    def run(self):
        print(f"\n{'='*60}")
        print(f"🔄 压力后恢复能力测试")
        print(f"{'='*60}")
        
        print("   阶段1: 施加高压...")
        for i in range(500):
            self.agent.submit_task('compute', {'stress': True, 'id': i})
            
        time.sleep(5)
        
        print("   阶段2: 停止压力，监控恢复...")
        process = psutil.Process()
        start_cpu = process.cpu_percent(interval=1.0)
        start_memory = process.memory_info().rss / 1024 / 1024
        
        recovery_checks = []
        for i in range(10):
            cpu = process.cpu_percent(interval=0.5)
            memory = process.memory_info().rss / 1024 / 1024
            recovery_checks.append({'cpu': cpu, 'memory': memory})
            time.sleep(1)
            
        final_cpu = recovery_checks[-1]['cpu']
        final_memory = recovery_checks[-1]['memory']
        
        print(f"   📊 CPU: {start_cpu:.1f}% -> {final_cpu:.1f}%")
        print(f"   📊 内存: {start_memory:.1f}MB -> {final_memory:.1f}MB")
        
        if final_cpu > 20:
            self.tracker.record_bug('no_cpu_recovery', 'medium', 
                                    f'CPU未恢复: 从{start_cpu:.1f}%到{final_cpu:.1f}%',
                                    component='recovery')
            
        status = self.agent.guardian_service.get_system_status()
        print(f"   🩺 系统健康: {status['overall_status']}")


def run_deep_tests():
    """运行极深度测试"""
    print("=" * 80)
    print("🚀 极深度压力测试框架 - 极限性能验证")
    print("=" * 80)
    
    tracker = DeepTestTracker()
    
    from main_loop_controller_orchestrator_system import MainLoopController
    
    print("\n📦 初始化Agent...")
    agent = MainLoopController()
    agent.initialize()
    agent.start()
    
    time.sleep(3)
    
    tests = [
        ExtremeConcurrencyTest(agent, tracker),
        PerformanceBottleneckTest(agent, tracker),
        StressRecoveryTest(agent, tracker),
        LongTermLeakTest(agent, tracker),
    ]
    
    test_names = [
        "极端并发压力",
        "性能瓶颈深度分析",
        "压力后恢复能力",
        "长时间内存泄漏检测",
    ]
    
    monitor_thread = threading.Thread(target=monitor_system, args=(agent, tracker), daemon=True)
    monitor_thread.start()
    
    print("\n🧪 开始运行极深度测试...")
    
    for i, (test, name) in enumerate(zip(tests, test_names)):
        try:
            test.run()
        except Exception as e:
            tracker.record_bug('test_failure', 'critical', 
                              f'{name} 测试失败: {str(e)}',
                              component='test_framework')
            
        time.sleep(2)
        
    generate_report(tracker, agent)
    
    agent.stop()


def monitor_system(agent, tracker):
    while True:
        try:
            process = psutil.Process()
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / 1024 / 1024
            threads = process.num_threads()
            
            tracker.track_metric('cpu_percent', cpu)
            tracker.track_metric('memory_mb', memory)
            tracker.track_metric('active_threads', threads)
            
            if cpu > 90:
                tracker.record_bug('extreme_cpu', 'medium', 
                                  f'极端高CPU: {cpu:.1f}%', component='system')
        except:
            pass
        time.sleep(1)


def generate_report(tracker: DeepTestTracker, agent):
    """生成深度测试报告"""
    print("\n" + "=" * 80)
    print("📋 极深度压力测试报告")
    print("=" * 80)
    
    elapsed = time.time() - tracker.start_time
    
    print(f"\n⏱️  测试时长: {elapsed/60:.1f}分钟")
    print(f"🔴 发现Bug总数: {len(tracker.bugs)}")
    
    bug_types = defaultdict(int)
    for bug in tracker.bugs:
        bug_types[f"{bug.type}:{bug.severity}"] += 1
        
    if bug_types:
        print(f"\n📊 Bug分布:")
        for key, count in sorted(bug_types.items(), key=lambda x: -x[1]):
            print(f"   {key}: {count}")
            
    print(f"\n📈 性能指标:")
    
    metrics_to_show = ['cpu_percent', 'memory_mb', 'active_threads']
    for metric_name in metrics_to_show:
        if metric_name in tracker.metrics_history and len(tracker.metrics_history[metric_name]) > 0:
            values = [m['value'] for m in tracker.metrics_history[metric_name]]
            avg = sum(values) / len(values)
            max_val = max(values)
            min_val = min(values)
            print(f"   {metric_name}:")
            print(f"      avg: {avg:.1f}, max: {max_val:.1f}, min: {min_val:.1f}")
            
    status = agent.get_system_status()
    print(f"\n🏥 系统状态:")
    print(f"   Guardian: {status['guardian']['overall_status']}")
    print(f"   完成任务: {status['statistics']['total_tasks']}")
    
    if tracker.bugs:
        print(f"\n🔴 严重Bug:")
        critical_bugs = [b for b in tracker.bugs if b.severity == 'critical']
        for bug in critical_bugs[:5]:
            print(f"\n   #{bug.id} [{bug.component}] {bug.type}")
            print(f"   {bug.message}")
            
    print("\n" + "=" * 80)
    print("✅ 极深度测试完成")
    print("=" * 80)


if __name__ == "__main__":
    run_deep_tests()
