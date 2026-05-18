#!/usr/bin/env python3
"""
超级深度压力测试框架 - 极限场景验证
包含: 30+分钟长时间运行, 极高并发, 异常注入, 边界条件, 内存泄漏测试
"""
import sys
import time
import random
import threading
import gc
import os
import psutil
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, field
import hashlib
import signal

sys.path.insert(0, '/workspace')


@dataclass
class DeepTestIssue:
    id: int
    type: str
    severity: str
    message: str
    stacktrace: str
    timestamp: float
    component: str


@dataclass
class PerformanceMetric:
    name: str
    timestamp: float
    value: float


class SuperDeepStressTester:
    """超级深度压力测试器"""
    
    def __init__(self):
        self.issues: List[DeepTestIssue] = []
        self.metrics: List[PerformanceMetric] = []
        self._lock = threading.Lock()
        self._issue_counter = 0
        self.running = True
        self.agent = None
        
    def record_issue(self, issue_type: str, severity: str, message: str, 
                     stacktrace: str = "", component: str = "system"):
        with self._lock:
            self._issue_counter += 1
            issue = DeepTestIssue(
                id=self._issue_counter,
                type=issue_type,
                severity=severity,
                message=message,
                stacktrace=stacktrace,
                timestamp=time.time(),
                component=component
            )
            self.issues.append(issue)
            return issue
    
    def record_metric(self, name: str, value: float):
        with self._lock:
            self.metrics.append(PerformanceMetric(
                name=name,
                timestamp=time.time(),
                value=value
            ))
    
    def run_extreme_concurrency_test(self, agent):
        """测试1: 极高并发压力 - 50-100线程"""
        print(f"\n{'='*80}")
        print(f"🚀 测试1: 极高并发压力 (50-100线程)")
        print(f"{'='*80}")
        
        for thread_count in [20, 50, 80, 100]:
            print(f"\n   🔹 测试并发数: {thread_count} 线程")
            threads = []
            tasks_submitted = [0]
            errors = [0]
            
            def concurrent_worker(worker_id):
                for i in range(30):
                    try:
                        agent.submit_task(
                            random.choice(['compute', 'process', 'analyze']),
                            {
                                'worker': worker_id,
                                'iter': i,
                                'data': [random.random() for _ in range(random.randint(1, 100))]
                            }
                        )
                        tasks_submitted[0] += 1
                        time.sleep(random.uniform(0.001, 0.01))
                    except Exception as e:
                        errors[0] += 1
                        if errors[0] <= 5:
                            self.record_issue(
                                "concurrency_error",
                                "critical",
                                f"Worker {worker_id} failed: {str(e)}",
                                traceback.format_exc() if 'traceback' in dir() else "",
                                "concurrent_worker"
                            )
            
            start_time = time.time()
            for i in range(thread_count):
                t = threading.Thread(target=concurrent_worker, args=(i,), daemon=True)
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            duration = time.time() - start_time
            throughput = tasks_submitted[0] / duration if duration > 0 else 0
            
            print(f"      提交任务: {tasks_submitted[0]}")
            print(f"      错误数: {errors[0]}")
            print(f"      耗时: {duration:.1f}秒")
            print(f"      吞吐量: {throughput:.1f}任务/秒")
            
            self.record_metric(f"concurrency_{thread_count}_throughput", throughput)
            self.record_metric(f"concurrency_{thread_count}_errors", errors[0])
            
            if errors[0] > 0:
                self.record_issue(
                    "concurrent_failure",
                    "high",
                    f"{thread_count}线程并发有{errors[0]}个错误",
                    "",
                    "concurrency_test"
                )
    
    def run_extreme_memory_test(self, agent, duration_minutes: int = 15):
        """测试2: 极端内存压力测试 - 15分钟"""
        print(f"\n{'='*80}")
        print(f"💾 测试2: 极端内存压力 (15分钟)")
        print(f"{'='*80}")
        
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        last_memory = baseline_memory
        
        print(f"   基准内存: {baseline_memory:.1f}MB")
        
        for minute in range(duration_minutes):
            elapsed_minutes = minute + 1
            
            for batch in range(3):
                for _ in range(50):
                    large_payload = {
                        'id': random.randint(0, 1000000),
                        'data': [
                            {'x': random.random(), 'y': random.random(), 'z': random.random()}
                            for _ in range(random.randint(1, 200))
                        ],
                        'metadata': {
                            'version': random.random(),
                            'timestamp': time.time()
                        }
                    }
                    agent.submit_task('process', large_payload)
                
                time.sleep(10)
            
            gc.collect()
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - baseline_memory
            memory_delta = current_memory - last_memory
            
            print(f"   📊 第{elapsed_minutes}分钟: {current_memory:.1f}MB (累计增长+{memory_growth:.1f}MB)")
            
            self.record_metric("memory_usage_mb", current_memory)
            self.record_metric("memory_growth_mb", memory_growth)
            
            if memory_growth > 50:
                self.record_issue(
                    "severe_memory_leak",
                    "critical",
                    f"内存严重泄漏: {memory_growth:.1f}MB在{elapsed_minutes}分钟内",
                    "",
                    "memory_test"
                )
            
            last_memory = current_memory
        
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"\n   📈 最终内存: {final_memory:.1f}MB, 总增长: +{final_memory - baseline_memory:.1f}MB")
    
    def run_boundary_conditions_test(self, agent):
        """测试3: 边界条件测试 - 各种极限输入"""
        print(f"\n{'='*80}")
        print(f"📊 测试3: 边界条件与极限输入")
        print(f"{'='*80}")
        
        boundary_cases = [
            ("empty_payload", ''),
            ("null_payload", None),
            ("very_deep_nesting", self._generate_deep_nesting(100)),
            ("extremely_large_string", 'x' * 100000),
            ("extremely_large_list", list(range(100000))),
            ("unicode_special_chars", ''.join(chr(i) for i in range(1000, 2000))),
            ("max_int", sys.maxsize),
            ("float_infinity", float('inf')),
            ("float_nan", float('nan')),
            ("complex_data_structure", self._generate_complex_structure())
        ]
        
        errors_found = 0
        
        for case_name, payload in boundary_cases:
            try:
                task_id = agent.submit_task('compute', payload)
                time.sleep(0.5)
                status = agent.execution_engine.get_task_status(task_id) if hasattr(agent, 'execution_engine') else None
                print(f"   🔹 {case_name}: OK, status={status}")
            except Exception as e:
                errors_found += 1
                print(f"   ❌ {case_name}: FAILED - {str(e)}")
                self.record_issue(
                    "boundary_condition_failure",
                    "critical",
                    f"边界条件 {case_name} 处理失败: {str(e)}",
                    traceback.format_exc() if 'traceback' in dir() else "",
                    "boundary_test"
                )
        
        if errors_found > 0:
            self.record_issue(
                "boundary_errors",
                "high",
                f"边界条件测试共发现{errors_found}个错误",
                "",
                "boundary_test"
            )
    
    def run_error_injection_test(self, agent):
        """测试4: 异常注入与恢复测试"""
        print(f"\n{'='*80}")
        print(f"⚠️ 测试4: 异常注入与恢复测试")
        print(f"{'='*80}")
        
        for _ in range(50):
            task_type = random.choice(['compute', 'process', 'analyze', 'invalid_type123', None])
            payload = {
                'error_injection': True,
                'timestamp': time.time(),
                'random_value': random.random()
            }
            
            try:
                if random.random() < 0.3:
                    payload = None
                elif random.random() < 0.1:
                    payload = "this is not a dict"
                
                agent.submit_task(task_type, payload)
            except Exception as e:
                self.record_issue(
                    "error_injection_crash",
                    "medium",
                    f"任务提交崩溃: type={task_type}, error={str(e)}",
                    traceback.format_exc() if 'traceback' in dir() else "",
                    "error_injection"
                )
        
        time.sleep(2)
        
        status = agent.get_system_status()
        if status['guardian']['overall_status'] == 'healthy':
            print("   ✅ 系统在异常注入后保持健康")
        else:
            self.record_issue(
                "system_unhealthy_after_error_injection",
                "critical",
                "异常注入后系统不健康",
                "",
                "error_injection_test"
            )
    
    def run_long_term_stability_test(self, agent, duration_minutes: int = 20):
        """测试5: 超长时间稳定性测试 - 20分钟"""
        print(f"\n{'='*80}")
        print(f"⏱️ 测试5: 超长时间稳定性 (20分钟)")
        print(f"{'='*80}")
        
        process = psutil.Process()
        start_time = time.time()
        
        total_tasks = 0
        
        for minute in range(duration_minutes):
            tasks_in_minute = 0
            
            for batch in range(4):
                for _ in range(25):
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        {
                            'test': 'long_term',
                            'minute': minute,
                            'batch': batch,
                            'idx': _,
                            'data': random.random()
                        }
                    )
                    tasks_in_minute += 1
                
                time.sleep(10)
            
            total_tasks += tasks_in_minute
            
            current_cpu = process.cpu_percent(interval=0.5)
            current_memory = process.memory_info().rss / 1024 / 1024
            
            self.record_metric("cpu_percent", current_cpu)
            self.record_metric("memory_mb", current_memory)
            
            elapsed = time.time() - start_time
            minutes_elapsed = int(elapsed / 60)
            print(f"   📊 {minutes_elapsed}分钟: CPU={current_cpu:.1f}%, 内存={current_memory:.1f}MB, 任务数={total_tasks}")
            
            if current_cpu > 90:
                self.record_issue(
                    "extreme_cpu_usage",
                    "medium",
                    f"极端CPU使用: {current_cpu:.1f}%",
                    "",
                    "long_term_test"
                )
        
        print(f"\n   📈 完成! 总任务数: {total_tasks}")
    
    def _generate_deep_nesting(self, depth: int):
        if depth <= 0:
            return "bottom"
        return {'nested': self._generate_deep_nesting(depth - 1)}
    
    def _generate_complex_structure(self):
        return {
            'level1': {
                'level2': {
                    'level3': {
                        'lists': [
                            [1, 2, 3],
                            [{'a': 'b'}, {'c': 'd'}],
                            list(range(100))
                        ],
                        'dict': {
                            'key1': 'value1',
                            'key2': 12345,
                            'key3': [True, False, None]
                        },
                        'deep': self._generate_deep_nesting(20)
                    }
                }
            },
            'simple': 'string',
            'number': 99999999999999,
            'boolean': True,
            'null': None
        }
    
    def generate_final_report(self, agent):
        """生成最终的测试报告"""
        print("\n" + "=" * 80)
        print("📋 超级深度压力测试报告")
        print("=" * 80)
        
        status = agent.get_system_status()
        print(f"\n🏥 最终系统状态:")
        print(f"   Guardian健康: {status['guardian']['overall_status']}")
        print(f"   完成任务: {status['statistics']['total_tasks']}")
        
        print(f"\n🔴 发现的问题 ({len(self.issues)}个):")
        
        critical_issues = [i for i in self.issues if i.severity == 'critical']
        high_issues = [i for i in self.issues if i.severity == 'high']
        medium_issues = [i for i in self.issues if i.severity == 'medium']
        
        print(f"   Critical: {len(critical_issues)}")
        print(f"   High: {len(high_issues)}")
        print(f"   Medium: {len(medium_issues)}")
        
        if critical_issues:
            print(f"\n   🔴 严重问题 (前10个):")
            for issue in critical_issues[:10]:
                print(f"      #{issue.id} [{issue.component}] {issue.type}: {issue.message}")
        
        print(f"\n📊 性能指标:")
        
        for metric_name in ["cpu_percent", "memory_mb", "memory_growth_mb"]:
            values = [m.value for m in self.metrics if m.name == metric_name]
            if values:
                avg_value = sum(values) / len(values)
                max_value = max(values)
                min_value = min(values)
                print(f"   {metric_name}:")
                print(f"      平均: {avg_value:.1f}, 最大: {max_value:.1f}, 最小: {min_value:.1f}")
        
        print("\n" + "=" * 80)
        print("✅ 超级深度压力测试完成")
        print("=" * 80)


def main():
    print("=" * 80)
    print("🚀 超级深度压力测试框架")
    print("=" * 80)
    
    tester = SuperDeepStressTester()
    
    from main_loop_controller_orchestrator_system import MainLoopController
    
    print("\n📦 初始化Agent...")
    agent = MainLoopController()
    agent.initialize()
    agent.start()
    
    time.sleep(3)
    
    print("\n🧪 开始超级深度测试...")
    
    try:
        tester.run_extreme_concurrency_test(agent)
        tester.run_boundary_conditions_test(agent)
        tester.run_error_injection_test(agent)
        tester.run_extreme_memory_test(agent, duration_minutes=15)
        tester.run_long_term_stability_test(agent, duration_minutes=20)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现严重错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        tester.record_issue(
            "test_framework_crash",
            "critical",
            f"测试框架崩溃: {str(e)}",
            traceback.format_exc() if 'traceback' in dir() else "",
            "main"
        )
    
    tester.generate_final_report(agent)
    
    print("\n🛑 停止Agent...")
    agent.stop()
    print("✅ Agent已停止")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 未预料的错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
