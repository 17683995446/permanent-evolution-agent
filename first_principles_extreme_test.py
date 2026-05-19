#!/usr/bin/env python3
"""
第一性原理极限测试框架
从系统核心功能出发，测试最极端的条件下的系统表现

核心测试场景：
1. 资源耗尽测试 - 测试系统在资源临界点的表现
2. 锁竞争测试 - 验证多线程下的锁安全性和性能
3. 边界突破测试 - 测试系统的极限处理能力
4. 级联失败测试 - 验证异常传播和恢复机制
5. 长时间极限运行 - 验证系统的长期稳定性
"""
import sys
import time
import random
import threading
import gc
import os
import psutil
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, field
import signal

sys.path.insert(0, '/workspace')


@dataclass
class ExtremeIssue:
    id: int
    category: str
    severity: str
    message: str
    details: Dict[str, Any]
    timestamp: float


@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_mb: float
    thread_count: int
    open_files: int
    tasks_completed: int
    errors: int


class FirstPrinciplesExtremeTester:
    """第一性原理极限测试器"""

    def __init__(self):
        self.issues: List[ExtremeIssue] = []
        self.metrics_history: List[SystemMetrics] = []
        self._lock = threading.Lock()
        self._issue_counter = 0
        self.agent = None
        self._stop_flag = threading.Event()
        self._test_results = {}

    def record_issue(self, category: str, severity: str, message: str, details: Dict[str, Any]):
        with self._lock:
            self._issue_counter += 1
            issue = ExtremeIssue(
                id=self._issue_counter,
                category=category,
                severity=severity,
                message=message,
                details=details,
                timestamp=time.time()
            )
            self.issues.append(issue)
            print(f"   ⚠️  [{category}] {message}")

    def record_metric(self, metric: SystemMetrics):
        with self._lock:
            self.metrics_history.append(metric)

    def get_baseline_metrics(self) -> Dict[str, float]:
        """获取系统基线指标"""
        process = psutil.Process()
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_mb': psutil.virtual_memory().total / 1024 / 1024,
            'baseline_memory_mb': process.memory_info().rss / 1024 / 1024,
            'baseline_threads': threading.active_count(),
            'baseline_files': len(process.open_files())
        }

    def test_resource_exhaustion(self, agent, duration_seconds: int = 180):
        """测试1: 资源耗尽测试 - 在资源临界点运行"""
        print(f"\n{'='*80}")
        print(f"🔥 测试1: 资源耗尽测试 ({duration_seconds}秒)")
        print(f"{'='*80}")

        baseline = self.get_baseline_metrics()
        print(f"   基线指标:")
        print(f"      CPU核心数: {baseline['cpu_count']}")
        print(f"      内存总量: {baseline['memory_total_mb']:.1f}MB")
        print(f"      基准内存: {baseline['baseline_memory_mb']:.1f}MB")
        print(f"      线程数: {baseline['baseline_threads']}")

        process = psutil.Process()
        start_time = time.time()
        task_count = 0
        error_count = 0

        while time.time() - start_time < duration_seconds:
            try:
                for _ in range(20):
                    payload = {
                        'id': random.randint(0, 1000000),
                        'data': [random.random() for _ in range(random.randint(1, 100))],
                        'timestamp': time.time()
                    }
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        payload
                    )
                    task_count += 1

                time.sleep(3)

                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - baseline['baseline_memory_mb']
                thread_count = threading.active_count()

                self.record_metric(SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=process.cpu_percent(interval=0.1),
                    memory_mb=current_memory,
                    thread_count=thread_count,
                    open_files=len(process.open_files()),
                    tasks_completed=task_count,
                    errors=error_count
                ))

                if memory_growth > 200:
                    self.record_issue(
                        "resource_exhaustion",
                        "critical",
                        f"内存增长异常: {memory_growth:.1f}MB",
                        {'memory_mb': current_memory, 'growth_mb': memory_growth}
                    )
                    gc.collect()

                if thread_count > 100:
                    self.record_issue(
                        "resource_exhaustion",
                        "warning",
                        f"线程数过多: {thread_count}",
                        {'thread_count': thread_count}
                    )

                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0:
                    print(f"      ⏱️  {int(elapsed)}秒: 内存={current_memory:.1f}MB, "
                          f"线程={thread_count}, 任务={task_count}")

            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    self.record_issue(
                        "resource_exhaustion",
                        "high",
                        f"执行错误: {str(e)}",
                        {'error': str(e), 'count': error_count}
                    )
                time.sleep(1)

        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"\n   📊 资源耗尽测试结果:")
        print(f"      总任务数: {task_count}")
        print(f"      错误数: {error_count}")
        print(f"      最终内存: {final_memory:.1f}MB")
        print(f"      内存增长: +{final_memory - baseline['baseline_memory_mb']:.1f}MB")

        self._test_results['resource_exhaustion'] = {
            'passed': error_count < task_count * 0.1,
            'task_count': task_count,
            'error_count': error_count,
            'memory_growth_mb': final_memory - baseline['baseline_memory_mb']
        }

    def test_lock_contention(self, agent, duration_seconds: int = 120):
        """测试2: 锁竞争测试 - 多线程高并发下的锁安全"""
        print(f"\n{'='*80}")
        print(f"🔒 测试2: 锁竞争测试 ({duration_seconds}秒)")
        print(f"{'='*80}")

        shared_data = {'counter': 0, 'errors': 0}
        lock = threading.Lock()
        workers = []
        worker_count = 50

        def lock_contention_worker(worker_id):
            for i in range(30):
                try:
                    with lock:
                        shared_data['counter'] += 1
                        value = shared_data['counter']

                    agent.submit_task(
                        random.choice(['compute', 'process']),
                        {'worker': worker_id, 'iter': i, 'value': value}
                    )
                    time.sleep(random.uniform(0.001, 0.01))

                except Exception as e:
                    with lock:
                        shared_data['errors'] += 1

        start_time = time.time()
        print(f"   启动 {worker_count} 个并发工作线程...")

        for i in range(worker_count):
            t = threading.Thread(target=lock_contention_worker, args=(i,), daemon=True)
            workers.append(t)
            t.start()

        expected_count = worker_count * 30
        initial_errors = shared_data['errors']

        while time.time() - start_time < duration_seconds:
            time.sleep(5)
            with lock:
                current_count = shared_data['counter']
                current_errors = shared_data['errors']
            print(f"      ⏱️  {int(time.time()-start_time)}秒: "
                  f"计数器={current_count}/{expected_count}, 错误={current_errors}")

        for t in workers:
            t.join(timeout=5)

        final_count = shared_data['counter']
        final_errors = shared_data['errors']

        consistency_check = abs(final_count - expected_count)
        error_rate = final_errors / (worker_count * 30) * 100

        print(f"\n   📊 锁竞争测试结果:")
        print(f"      预期操作: {expected_count}")
        print(f"      实际计数: {final_count}")
        print(f"      计数误差: {consistency_check}")
        print(f"      错误数: {final_errors}")
        print(f"      错误率: {error_rate:.2f}%")

        if consistency_check > worker_count * 3:
            self.record_issue(
                "lock_contention",
                "high",
                f"计数器不一致: 预期{final_count}, 实际{final_count}",
                {'expected': expected_count, 'actual': final_count}
            )

        if error_rate > 5:
            self.record_issue(
                "lock_contention",
                "warning",
                f"高错误率: {error_rate:.2f}%",
                {'error_rate': error_rate}
            )

        self._test_results['lock_contention'] = {
            'passed': error_rate < 1,
            'error_rate': error_rate,
            'consistency_check': consistency_check
        }

    def test_boundary_conditions(self, agent):
        """测试3: 边界突破测试 - 测试系统极限处理能力"""
        print(f"\n{'='*80}")
        print(f"📊 测试3: 边界突破测试")
        print(f"{'='*80}")

        boundary_cases = [
            ("极空负载", {}, 10),
            ("超深嵌套", {'level': 0}, 50),
            ("超大列表", {'data': list(range(10000))}, 20),
            ("极大字符串", {'text': 'x' * 1000000}, 10),
            ("特殊Unicode", {'chars': ''.join(chr(i) for i in range(5000, 6000))}, 10),
            ("极端数字", {'max_int': sys.maxsize, 'min_int': -sys.maxsize}, 20),
            ("浮点极限", {'inf': float('inf'), 'neg_inf': float('-inf'), 'nan': float('nan')}, 20),
            ("空字符串", {'': ''}, 10),
            ("None值", {'value': None}, 10),
            ("循环引用", {'self_ref': None}, 5),
        ]

        total_tests = 0
        failed_tests = 0

        for case_name, payload_template, repeat_count in boundary_cases:
            for i in range(repeat_count):
                total_tests += 1
                try:
                    dynamic_payload = self._generate_dynamic_payload(payload_template, i)
                    task_id = agent.submit_task('compute', dynamic_payload)
                    time.sleep(0.1)

                    if i == 0:
                        print(f"   ✅ {case_name}: 通过")

                except Exception as e:
                    failed_tests += 1
                    if failed_tests <= 10:
                        self.record_issue(
                            "boundary_conditions",
                            "high",
                            f"{case_name} 失败: {str(e)}",
                            {'case': case_name, 'error': str(e)}
                        )
                    print(f"   ❌ {case_name}: {str(e)}")

        print(f"\n   📊 边界测试结果:")
        print(f"      总测试数: {total_tests}")
        print(f"      失败数: {failed_tests}")
        print(f"      通过率: {(total_tests - failed_tests) / total_tests * 100:.1f}%")

        self._test_results['boundary_conditions'] = {
            'passed': failed_tests < total_tests * 0.1,
            'total_tests': total_tests,
            'failed_tests': failed_tests
        }

    def _generate_dynamic_payload(self, template: Dict, iteration: int):
        """生成动态payload"""
        payload = {}
        for key, value in template.items():
            if isinstance(value, int) and value == 0 and key == 'level':
                payload[key] = iteration
            elif isinstance(value, list):
                payload[key] = value[:min(100, len(value))]
            else:
                payload[key] = value
        payload['iteration'] = iteration
        return payload

    def test_cascading_failures(self, agent, duration_seconds: int = 120):
        """测试4: 级联失败测试 - 验证异常传播和恢复"""
        print(f"\n{'='*80}")
        print(f"⚠️ 测试4: 级联失败测试 ({duration_seconds}秒)")
        print(f"{'='*80}")

        injection_count = 0
        recovery_count = 0
        system_failures = 0

        invalid_types = [None, '', 'INVALID_TYPE_123', 123, [], {}]
        invalid_payloads = [None, '', 123, [], 'invalid_json_structure']

        start_time = time.time()

        for i in range(duration_seconds):
            try:
                if i % 3 == 0:
                    invalid_type = random.choice(invalid_types)
                    agent.submit_task(invalid_type, {'test': i})
                    injection_count += 1

                if i % 5 == 0:
                    invalid_payload = random.choice(invalid_payloads)
                    agent.submit_task('compute', invalid_payload)
                    injection_count += 1

                if i % 7 == 0:
                    agent.submit_task('compute', None)
                    injection_count += 1

                time.sleep(1)

                try:
                    status = agent.get_system_status()
                    if status['guardian']['overall_status'] == 'healthy':
                        recovery_count += 1
                except Exception as e:
                    system_failures += 1
                    if system_failures <= 5:
                        self.record_issue(
                            "cascading_failures",
                            "critical",
                            f"系统状态获取失败: {str(e)}",
                            {'iteration': i, 'error': str(e)}
                        )

                if (i + 1) % 20 == 0:
                    print(f"      ⏱️  {i+1}秒: 注入={injection_count}, "
                          f"恢复={recovery_count}, 系统故障={system_failures}")

            except Exception as e:
                system_failures += 1
                if system_failures <= 5:
                    self.record_issue(
                        "cascading_failures",
                        "high",
                        f"级联失败: {str(e)}",
                        {'iteration': i, 'error': str(e)}
                    )

        final_status = agent.get_system_status()
        final_health = final_status['guardian']['overall_status']

        print(f"\n   📊 级联失败测试结果:")
        print(f"      总注入次数: {injection_count}")
        print(f"      成功恢复: {recovery_count}")
        print(f"      系统故障: {system_failures}")
        print(f"      最终健康状态: {final_health}")

        if final_health != 'healthy':
            self.record_issue(
                "cascading_failures",
                "critical",
                f"系统未能恢复正常状态",
                {'final_health': final_health}
            )

        recovery_rate = recovery_count / duration_seconds * 100 if duration_seconds > 0 else 0
        self._test_results['cascading_failures'] = {
            'passed': final_health == 'healthy' and system_failures < injection_count * 0.5,
            'injection_count': injection_count,
            'recovery_rate': recovery_rate
        }

    def test_long_term_stability(self, agent, duration_seconds: int = 600):
        """测试5: 长时间极限运行 - 验证系统长期稳定性"""
        print(f"\n{'='*80}")
        print(f"⏱️ 测试5: 长时间极限运行 ({duration_seconds}秒 = {duration_seconds/60:.0f}分钟)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        baseline_threads = threading.active_count()

        start_time = time.time()
        total_tasks = 0
        total_errors = 0
        checkpoints = []

        print(f"   基线: 内存={baseline_memory:.1f}MB, 线程={baseline_threads}")

        checkpoint_interval = duration_seconds // 10

        for second in range(duration_seconds):
            try:
                batch_size = random.randint(10, 30)
                for _ in range(batch_size):
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        {
                            'timestamp': time.time(),
                            'iteration': second,
                            'random': random.random(),
                            'data': [i for i in range(random.randint(1, 50))]
                        }
                    )
                    total_tasks += 1

                if second % 30 == 0:
                    gc.collect()

                current_time = time.time()
                elapsed = current_time - start_time

                if elapsed >= (len(checkpoints) + 1) * checkpoint_interval:
                    checkpoint_time = elapsed
                    current_memory = process.memory_info().rss / 1024 / 1024
                    current_threads = threading.active_count()
                    memory_growth = current_memory - baseline_memory

                    status = agent.get_system_status()
                    checkpoint = {
                        'time': checkpoint_time,
                        'memory_mb': current_memory,
                        'memory_growth_mb': memory_growth,
                        'threads': current_threads,
                        'tasks': total_tasks,
                        'health': status['guardian']['overall_status']
                    }
                    checkpoints.append(checkpoint)

                    print(f"      📍 {len(checkpoints)*10}% ({int(checkpoint_time)}秒): "
                          f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                          f"线程={current_threads}, 任务={total_tasks}")

                time.sleep(1)

            except Exception as e:
                total_errors += 1
                if total_errors <= 10:
                    self.record_issue(
                        "long_term_stability",
                        "high",
                        f"长时间运行错误: {str(e)}",
                        {'second': second, 'error': str(e)}
                    )
                time.sleep(0.1)

        final_memory = process.memory_info().rss / 1024 / 1024
        final_threads = threading.active_count()
        final_status = agent.get_system_status()

        avg_memory = sum(c['memory_mb'] for c in checkpoints) / len(checkpoints) if checkpoints else final_memory
        memory_variance = sum((c['memory_mb'] - avg_memory) ** 2 for c in checkpoints) / len(checkpoints) if checkpoints else 0
        memory_stddev = memory_variance ** 0.5

        print(f"\n   📊 长时间运行测试结果:")
        print(f"      总任务数: {total_tasks}")
        print(f"      总错误数: {total_errors}")
        print(f"      错误率: {total_errors/total_tasks*100 if total_tasks > 0 else 0:.2f}%")
        print(f"      最终内存: {final_memory:.1f}MB")
        print(f"      内存增长: +{final_memory - baseline_memory:.1f}MB")
        print(f"      最终线程: {final_threads}")
        print(f"      最终健康: {final_status['guardian']['overall_status']}")
        print(f"      内存标准差: {memory_stddev:.2f}MB")

        if final_memory - baseline_memory > 500:
            self.record_issue(
                "long_term_stability",
                "critical",
                f"内存泄漏严重: +{final_memory - baseline_memory:.1f}MB",
                {'baseline': baseline_memory, 'final': final_memory, 'growth': final_memory - baseline_memory}
            )

        if total_errors / total_tasks > 0.05 if total_tasks > 0 else False:
            self.record_issue(
                "long_term_stability",
                "high",
                f"高错误率: {total_errors/total_tasks*100:.2f}%",
                {'errors': total_errors, 'tasks': total_tasks}
            )

        self._test_results['long_term_stability'] = {
            'passed': total_errors / total_tasks < 0.05 if total_tasks > 0 else False,
            'total_tasks': total_tasks,
            'total_errors': total_errors,
            'memory_growth_mb': final_memory - baseline_memory,
            'checkpoints': checkpoints
        }

    def analyze_results(self):
        """分析测试结果"""
        print("\n" + "=" * 80)
        print("📋 第一性原理极限测试 - 最终分析报告")
        print("=" * 80)

        total_issues = len(self.issues)
        critical_issues = [i for i in self.issues if i.severity == 'critical']
        high_issues = [i for i in self.issues if i.severity == 'high']
        warning_issues = [i for i in self.issues if i.severity == 'warning']

        print(f"\n📊 测试统计:")
        print(f"   总问题数: {total_issues}")
        print(f"   🔴 Critical: {len(critical_issues)}")
        print(f"   🟠 High: {len(high_issues)}")
        print(f"   🟡 Warning: {len(warning_issues)}")

        print(f"\n📊 测试结果汇总:")
        for test_name, result in self._test_results.items():
            status = "✅ 通过" if result.get('passed', False) else "❌ 失败"
            print(f"   {test_name}: {status}")

        if critical_issues:
            print(f"\n🔴 严重问题 (需要立即修复):")
            for issue in critical_issues[:10]:
                print(f"   #{issue.id} [{issue.category}] {issue.message}")
                print(f"      详情: {issue.details}")

        if high_issues:
            print(f"\n🟠 高优先级问题:")
            for issue in high_issues[:10]:
                print(f"   #{issue.id} [{issue.category}] {issue.message}")

        if self.metrics_history:
            avg_cpu = sum(m.cpu_percent for m in self.metrics_history) / len(self.metrics_history)
            max_cpu = max(m.cpu_percent for m in self.metrics_history)
            avg_memory = sum(m.memory_mb for m in self.metrics_history) / len(self.metrics_history)
            max_memory = max(m.memory_mb for m in self.metrics_history)

            print(f"\n📈 性能指标分析:")
            print(f"   CPU使用率: 平均={avg_cpu:.1f}%, 峰值={max_cpu:.1f}%")
            print(f"   内存使用: 平均={avg_memory:.1f}MB, 峰值={max_memory:.1f}MB")

        print("\n" + "=" * 80)
        if total_issues == 0:
            print("🎉 所有极限测试通过！系统表现优秀")
        elif len(critical_issues) == 0:
            print(f"⚠️ 测试完成，发现{total_issues}个问题（无严重问题）")
        else:
            print(f"🚨 测试完成，发现{len(critical_issues)}个严重问题需要修复")
        print("=" * 80)

        return total_issues, len(critical_issues)


def main():
    print("=" * 80)
    print("🔥 第一性原理极限测试框架")
    print("=" * 80)
    print("从系统核心功能出发，测试最极端的条件")

    tester = FirstPrinciplesExtremeTester()

    try:
        from main_loop_controller_orchestrator_system import MainLoopController

        print("\n📦 初始化Agent...")
        agent = MainLoopController()
        agent.initialize()
        agent.start()
        tester.agent = agent

        time.sleep(3)

        print("\n🚀 开始第一性原理极限测试...")
        print("   预计总时长: 约18分钟")
        print("   1. 资源耗尽测试: 3分钟")
        print("   2. 锁竞争测试: 2分钟")
        print("   3. 边界突破测试: 2分钟")
        print("   4. 级联失败测试: 2分钟")
        print("   5. 长时间极限运行: 10分钟")

        try:
            tester.test_resource_exhaustion(agent, duration_seconds=180)
            tester.test_lock_contention(agent, duration_seconds=120)
            tester.test_boundary_conditions(agent)
            tester.test_cascading_failures(agent, duration_seconds=120)
            tester.test_long_term_stability(agent, duration_seconds=600)

        except Exception as e:
            print(f"\n❌ 测试过程中出现严重错误: {str(e)}")
            print(traceback.format_exc())
            tester.record_issue(
                "test_framework",
                "critical",
                f"测试框架崩溃: {str(e)}",
                {'error': str(e), 'traceback': traceback.format_exc()}
            )

        total_issues, critical_count = tester.analyze_results()

        print("\n🛑 停止Agent...")
        agent.stop()
        print("✅ Agent已停止")

        return critical_count

    except Exception as e:
        print(f"\n❌ 测试初始化失败: {str(e)}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    try:
        critical_issues = main()
        sys.exit(1 if critical_issues > 0 else 0)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 未预料的错误: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)
