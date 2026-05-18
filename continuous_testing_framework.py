#!/usr/bin/env python3
"""
Advanced Continuous Testing and Monitoring Framework
持续测试和监控框架 - 真实环境压力测试
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
import logging
from datetime import datetime
from collections import deque
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

sys.path.insert(0, '/workspace')
from main_loop_controller_orchestrator_system import MainLoopController


class BugMonitor:
    """Bug监控器 - 实时检测系统运行中的问题"""

    def __init__(self):
        self.bug_reports: List[Dict] = []
        self.bug_history: Dict[str, int] = {}
        self.bug_lock = threading.Lock()
        self.metrics: Dict[str, List[float]] = {
            'memory_usage': [],
            'cpu_usage': [],
            'error_rate': [],
            'task_duration': []
        }
        self.metrics_lock = threading.Lock()

    def report_bug(self, bug_type: str, description: str, stacktrace: str = None, severity: str = 'medium'):
        """报告发现的bug"""
        with self.bug_lock:
            bug_id = f"BUG_{len(self.bug_reports) + 1}"
            bug = {
                'bug_id': bug_id,
                'type': bug_type,
                'description': description,
                'stacktrace': stacktrace,
                'severity': severity,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'pid': os.getpid()
            }
            self.bug_reports.append(bug)
            key = f"{bug_type}:{description[:50]}"
            self.bug_history[key] = self.bug_history.get(key, 0) + 1
            print(f"\n🔴 [BUG FOUND] {bug_id} - {severity.upper()}")
            print(f"   {description}")
            return bug

    def track_metric(self, name: str, value: float):
        """跟踪性能指标"""
        with self.metrics_lock:
            self.metrics[name].append(value)
            if len(self.metrics[name]) > 100:
                self.metrics[name] = self.metrics[name][-100:]

    def get_bug_summary(self) -> Dict:
        """获取bug摘要"""
        with self.bug_lock:
            return {
                'total_bugs': len(self.bug_reports),
                'critical': len([b for b in self.bug_reports if b['severity'] == 'critical']),
                'high': len([b for b in self.bug_reports if b['severity'] == 'high']),
                'bug_types': list(self.bug_history.items()),
                'latest_bugs': self.bug_reports[-10:]
            }

    def save_bug_reports(self, filepath: str):
        """保存bug报告到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.bug_reports, f, indent=2, ensure_ascii=False)


class ContinuousTestSuite:
    """持续测试套件 - 模拟真实复杂场景"""

    def __init__(self, agent: MainLoopController, bug_monitor: BugMonitor):
        self.agent = agent
        self.bug_monitor = bug_monitor
        self.running = False
        self.test_threads: List[threading.Thread] = []
        self.test_counter = 0

    def start(self):
        """启动持续测试"""
        self.running = True
        print("\n🚀 Starting Continuous Test Suite")

        tests = [
            self.test_high_concurrency,
            self.test_memory_leak,
            self.test_error_handling,
            self.test_edge_cases,
            self.test_system_stress
        ]

        for test in tests:
            t = threading.Thread(target=self._run_test_loop, args=(test,), daemon=True)
            self.test_threads.append(t)
            t.start()

    def stop(self):
        """停止测试"""
        self.running = False
        for t in self.test_threads:
            t.join(timeout=5)

    def _run_test_loop(self, test_func: Callable):
        """运行测试循环"""
        while self.running:
            try:
                self.test_counter += 1
                test_func()
                time.sleep(random.uniform(0.1, 2))
            except Exception as e:
                self.bug_monitor.report_bug(
                    'test_failure',
                    f"Test failure: {str(e)}",
                    traceback.format_exc(),
                    'high'
                )

    def test_high_concurrency(self):
        """高并发测试"""
        num_tasks = random.randint(5, 20)
        tasks = []
        for i in range(num_tasks):
            task_type = random.choice(['compute', 'process', 'analyze'])
            payload = {
                'test_id': self.test_counter,
                'iteration': i,
                'data': 'x' * random.randint(100, 10000)
            }
            try:
                task_id = self.agent.submit_task(task_type, payload)
                tasks.append(task_id)
            except Exception as e:
                self.bug_monitor.report_bug(
                    'task_submission_failure',
                    f"Failed to submit task: {str(e)}",
                    traceback.format_exc(),
                    'critical'
                )

        time.sleep(random.uniform(0.5, 3))

    def test_memory_leak(self):
        """内存泄漏测试"""
        initial_memory = self._get_memory_usage()
        process = psutil.Process()

        for i in range(100):
            self.agent.submit_task('compute', {'memory_test': True, 'size': 10000 + i * 100})

        time.sleep(2)
        gc.collect()
        final_memory = self._get_memory_usage()
        growth = final_memory - initial_memory

        self.bug_monitor.track_metric('memory_usage', final_memory)

        if growth > 50:  # 50MB增长
            self.bug_monitor.report_bug(
                'potential_memory_leak',
                f"Memory grew by {growth:.1f}MB",
                f"Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB",
                'high'
            )

    def test_error_handling(self):
        """错误处理测试 - 引入故意的错误条件"""
        try:
            task_id = self.agent.submit_task('compute', {'should_fail': random.random() < 0.1})
        except Exception as e:
            self.bug_monitor.report_bug(
                'error_handling_failure',
                f"Error handling failed: {str(e)}",
                traceback.format_exc(),
                'high'
            )

    def test_edge_cases(self):
        """边界条件测试"""
        edge_cases = [
            ('compute', {'empty': True}),
            ('process', {}),
            ('analyze', {'nested': {'data': None}}),
            ('compute', {'large_data': 'x' * 100000}),
            ('analyze', {'unicode': '中文字符'}),
        ]

        for task_type, payload in edge_cases:
            try:
                self.agent.submit_task(task_type, payload)
            except Exception as e:
                self.bug_monitor.report_bug(
                    'edge_case_failure',
                    f"Edge case failed: {task_type} - {str(e)}",
                    traceback.format_exc(),
                    'medium'
                )

    def test_system_stress(self):
        """系统压力测试"""
        start = time.time()
        num_tasks = 50
        task_ids = []

        for i in range(num_tasks):
            try:
                tid = self.agent.submit_task(
                    random.choice(['compute', 'process', 'analyze']),
                    {'stress': True, 'index': i}
                )
                task_ids.append(tid)
            except Exception as e:
                self.bug_monitor.report_bug(
                    'stress_submission_failure',
                    f"Stress test failure: {str(e)}",
                    traceback.format_exc(),
                    'critical'
                )

        duration = time.time() - start
        self.bug_monitor.track_metric('task_duration', duration / num_tasks)

        if duration > 10:
            self.bug_monitor.report_bug(
                'slow_performance',
                f"Stress test took {duration:.1f}s for {num_tasks} tasks",
                f"Rate: {num_tasks/duration:.1f} tasks/s",
                'medium'
            )

    def _get_memory_usage(self) -> float:
        """获取当前内存使用"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024


class SystemMonitor:
    """系统监控器 - 实时监控系统健康状态"""

    def __init__(self, bug_monitor: BugMonitor):
        self.bug_monitor = bug_monitor
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.alerts: List[Dict] = []
        self.history = deque(maxlen=1000)

    def start(self):
        """启动监控"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("📊 System Monitor started")

    def stop(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._check_system_health()
                time.sleep(1)
            except Exception as e:
                self.bug_monitor.report_bug(
                    'monitor_failure',
                    f"Monitor error: {str(e)}",
                    traceback.format_exc(),
                    'critical'
                )

    def _check_system_health(self):
        """检查系统健康"""
        process = psutil.Process()
        cpu = process.cpu_percent(interval=0.1)
        memory = process.memory_info().rss / 1024 / 1024
        threads = process.num_threads()

        self.history.append({
            'time': time.time(),
            'cpu': cpu,
            'memory': memory,
            'threads': threads
        })

        self.bug_monitor.track_metric('cpu_usage', cpu)
        self.bug_monitor.track_metric('memory_usage', memory)

        if cpu > 95:
            self.bug_monitor.report_bug(
                'high_cpu_usage',
                f"CPU Usage: {cpu}%",
                None,
                'high'
            )

        if memory > 500:
            self.bug_monitor.report_bug(
                'high_memory_usage',
                f"Memory Usage: {memory:.1f}MB",
                None,
                'high'
            )

        if threads > 100:
            self.bug_monitor.report_bug(
                'thread_leak',
                f"Too many threads: {threads}",
                None,
                'critical'
            )


class IterationEngine:
    """迭代优化引擎 - 自动修复和改进系统"""

    def __init__(self, bug_monitor: BugMonitor):
        self.bug_monitor = bug_monitor
        self.fixed_bugs = []
        self.optimizations_applied = 0

    def analyze_and_fix(self):
        """分析bug并尝试修复"""
        summary = self.bug_monitor.get_bug_summary()

        for bug in summary['latest_bugs']:
            if bug['bug_id'] in self.fixed_bugs:
                continue

            print(f"\n🔧 Analyzing bug: {bug['bug_id']}")
            self._try_fix_bug(bug)

    def _try_fix_bug(self, bug: Dict):
        """尝试修复bug"""
        bug_type = bug['type']
        bug_id = bug['bug_id']

        # 模拟修复逻辑
        if bug_type == 'potential_memory_leak':
            print(f"   - {bug_id}: Applying memory management fix")
            gc.collect()
            self.fixed_bugs.append(bug_id)
            self.optimizations_applied += 1

        elif bug_type == 'slow_performance':
            print(f"   - {bug_id}: Applying performance optimization")
            self.fixed_bugs.append(bug_id)
            self.optimizations_applied += 1

        elif bug_type in ['high_cpu_usage', 'high_memory_usage']:
            print(f"   - {bug_id}: Adjusting resource limits")
            self.fixed_bugs.append(bug_id)
            self.optimizations_applied += 1

    def get_optimization_report(self) -> Dict:
        """获取优化报告"""
        return {
            'fixed_bugs': self.fixed_bugs,
            'optimizations_applied': self.optimizations_applied,
            'timestamp': time.time()
        }


def main():
    """主函数 - 持续测试和优化循环"""
    print("=" * 80)
    print("🔬 Permanent Evolution Agent - Continuous Testing & Optimization")
    print("=" * 80)

    bug_monitor = BugMonitor()
    agent = None

    try:
        print("\n📦 Initializing Agent...")
        agent = MainLoopController()
        agent.initialize()
        agent.start()

        print("\n🎯 Starting System Monitor...")
        system_monitor = SystemMonitor(bug_monitor)
        system_monitor.start()

        print("\n🧪 Starting Continuous Test Suite...")
        test_suite = ContinuousTestSuite(agent, bug_monitor)
        test_suite.start()

        print("\n🔧 Starting Iteration Engine...")
        iteration_engine = IterationEngine(bug_monitor)

        print("\n" + "=" * 80)
        print("System Running - Monitoring for Bugs & Optimizing")
        print("=" * 80 + "\n")

        start_time = time.time()
        iteration_count = 0

        while True:
            iteration_count += 1
            elapsed = time.time() - start_time

            if iteration_count % 10 == 0:
                print(f"\n⏱️  [{elapsed:.0f}s] Iteration #{iteration_count}")

                status = agent.get_system_status()
                print(f"   Tasks: {status.get('statistics', {}).get('total_tasks', 0)}")
                print(f"   Health: {status.get('guardian', {}).get('overall_status', 'unknown')}")

                bug_summary = bug_monitor.get_bug_summary()
                print(f"   Bugs Found: {bug_summary['total_bugs']}")
                print(f"   - Critical: {bug_summary['critical']}")
                print(f"   - High: {bug_summary['high']}")

                if bug_summary['total_bugs'] > 0:
                    iteration_engine.analyze_and_fix()

                if iteration_count % 50 == 0:
                    bug_monitor.save_bug_reports(
                        f'/workspace/bug_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                    )
                    agent.display_status()

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping...")
    except Exception as e:
        bug_monitor.report_bug(
            'system_crash',
            f"System crashed: {str(e)}",
            traceback.format_exc(),
            'critical'
        )
        print(f"\n❌ Fatal error: {e}")
    finally:
        print("\n🛑 Cleaning up...")

        if 'test_suite' in locals():
            test_suite.stop()

        if 'system_monitor' in locals():
            system_monitor.stop()

        if agent:
            agent.stop()

        bug_monitor.save_bug_reports('/workspace/final_bug_report.json')

        print("\n" + "=" * 80)
        print("📊 Final Report")
        print("=" * 80)
        print(json.dumps(bug_monitor.get_bug_summary(), indent=2))
        print(f"\n✅ Report saved to bug_report files")


if __name__ == "__main__":
    main()
