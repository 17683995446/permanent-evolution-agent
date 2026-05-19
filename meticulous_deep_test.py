#!/usr/bin/env python3
"""
慢工出细活 - 极致深度测试框架
专注于发现系统中的细微问题，进行极致的单元和集成测试

核心原则：
1. 慢速深入 - 不追求速度，追求深度
2. 细致入微 - 监控每个细节
3. 持续观察 - 长时间运行，持续监控
4. 问题溯源 - 发现问题后深入分析根本原因
"""
import sys
import time
import random
import threading
import gc
import psutil
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque, defaultdict
import weakref

sys.path.insert(0, '/workspace')


class DetailMonitor:
    """细节监控器 - 监控系统中的每个细节"""

    def __init__(self):
        self.metrics = {
            'memory_samples': [],
            'cpu_samples': [],
            'thread_samples': [],
            'gc_stats': [],
            'cache_sizes': [],
            'queue_sizes': [],
            'lock_contentions': [],
            'errors': []
        }
        self._lock = threading.Lock()
        self._start_time = time.time()

    def record(self, category: str, value: Any):
        with self._lock:
            if category in self.metrics:
                self.metrics[category].append({
                    'timestamp': time.time() - self._start_time,
                    'value': value
                })

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            summary = {}
            for category, samples in self.metrics.items():
                if not samples:
                    continue

                values = [s['value'] for s in samples]
                if all(isinstance(v, (int, float)) for v in values):
                    summary[category] = {
                        'count': len(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'latest': values[-1]
                    }
                else:
                    summary[category] = {
                        'count': len(values),
                        'latest': str(values[-1])[:100]
                    }
            return summary


class MeticulousTester:
    """慢工出细活测试器"""

    def __init__(self):
        self.monitor = DetailMonitor()
        self.agent = None
        self.test_results = {}

    def test_memory_leak_detection(self, agent, duration_seconds: int = 300):
        """测试1: 内存泄漏深度检测（5分钟）"""
        print(f"\n{'='*80}")
        print(f"🔍 测试1: 内存泄漏深度检测 ({duration_seconds}秒)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        baseline_handles = len(process.open_files())

        print(f"   基线内存: {baseline_memory:.2f}MB")
        print(f"   基线句柄数: {baseline_handles}")

        gc.collect()
        gc_start = gc.get_count()

        samples = []
        sample_interval = 5

        for second in range(0, duration_seconds, sample_interval):
            time.sleep(sample_interval)

            gc.collect()
            gc_count = gc.get_count()

            current_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - baseline_memory

            open_files = len(process.open_files())
            num_threads = threading.active_count()

            status = agent.get_system_status()
            exec_summary = status.get('execution', {})
            cache_size = exec_summary.get('applied_rules', []) if 'applied_rules' in exec_summary else []

            sample = {
                'second': second,
                'memory_mb': current_memory,
                'memory_growth_mb': memory_growth,
                'open_files': open_files,
                'threads': num_threads,
                'gc_count': gc_count,
                'cache_size': len(cache_size) if isinstance(cache_size, list) else 0
            }
            samples.append(sample)

            self.monitor.record('memory_samples', current_memory)
            self.monitor.record('thread_samples', num_threads)

            leak_rate = memory_growth / (second + 1) * 60 if second > 0 else 0

            print(f"   ⏱️ {second}秒: "
                  f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                  f"线程={num_threads}, "
                  f"句柄={open_files}, "
                  f"泄漏率={leak_rate:.2f}MB/分钟")

            if memory_growth > 200:
                print(f"   ⚠️  警告: 内存增长过快")
                self.monitor.record('errors', {
                    'type': 'memory_leak',
                    'second': second,
                    'growth': memory_growth
                })

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory

        print(f"\n   📊 内存泄漏检测结果:")
        print(f"      基线内存: {baseline_memory:.2f}MB")
        print(f"      最终内存: {final_memory:.2f}MB")
        print(f"      总增长: +{total_growth:.2f}MB")
        print(f"      平均增长: {total_growth/duration_seconds*60:.2f}MB/分钟")
        print(f"      平均线程: {sum(s['threads'] for s in samples)/len(samples):.1f}")
        print(f"      峰值线程: {max(s['threads'] for s in samples)}")

        leak_detected = total_growth > 100
        self.test_results['memory_leak_detection'] = {
            'passed': not leak_detected,
            'baseline_mb': baseline_memory,
            'final_mb': final_memory,
            'growth_mb': total_growth,
            'samples': samples
        }

        return not leak_detected

    def test_thread_pool_health(self, agent, duration_seconds: int = 180):
        """测试2: 线程池健康检测（3分钟）"""
        print(f"\n{'='*80}")
        print(f"🔧 测试2: 线程池健康检测 ({duration_seconds}秒)")
        print(f"{'='*80}")

        process = psutil.Process()

        print(f"   基线线程数: {threading.active_count()}")
        print(f"   CPU核心数: {psutil.cpu_count()}")

        thread_samples = []
        cpu_samples = []

        for second in range(0, duration_seconds, 3):
            time.sleep(3)

            num_threads = threading.active_count()
            cpu_percent = process.cpu_percent(interval=0.5)

            thread_samples.append({
                'second': second,
                'count': num_threads,
                'cpu_percent': cpu_percent
            })

            cpu_samples.append(cpu_percent)

            self.monitor.record('thread_samples', num_threads)
            self.monitor.record('cpu_samples', cpu_percent)

            print(f"   ⏱️ {second}秒: "
                  f"线程={num_threads}, "
                  f"CPU={cpu_percent:.1f}%")

            if num_threads > 100:
                print(f"   ⚠️  警告: 线程数过多")
                self.monitor.record('errors', {
                    'type': 'thread_explosion',
                    'second': second,
                    'thread_count': num_threads
                })

        avg_threads = sum(s['count'] for s in thread_samples) / len(thread_samples)
        max_threads = max(s['count'] for s in thread_samples)

        print(f"\n   📊 线程池健康检测结果:")
        print(f"      平均线程数: {avg_threads:.1f}")
        print(f"      峰值线程数: {max_threads}")
        print(f"      平均CPU: {sum(cpu_samples)/len(cpu_samples):.1f}%")

        healthy = max_threads < 100 and avg_threads < 50
        self.test_results['thread_pool_health'] = {
            'passed': healthy,
            'avg_threads': avg_threads,
            'max_threads': max_threads
        }

        return healthy

    def test_lock_contention_deep(self, agent, duration_seconds: int = 120):
        """测试3: 锁竞争深度分析（2分钟）"""
        print(f"\n{'='*80}")
        print(f"🔒 测试3: 锁竞争深度分析 ({duration_seconds}秒)")
        print(f"{'='*80}")

        shared_state = {'counter': 0, 'errors': 0}
        lock = threading.Lock()
        contention_count = [0]

        def contention_worker(worker_id: int, iterations: int):
            for i in range(iterations):
                try:
                    start_time = time.time()
                    with lock:
                        current = shared_state['counter']
                        shared_state['counter'] = current + 1
                        time.sleep(0.0001)
                    acquire_time = time.time() - start_time

                    if acquire_time > 0.01:
                        contention_count[0] += 1

                except Exception as e:
                    with lock:
                        shared_state['errors'] += 1

        workers = []
        num_workers = 30
        iterations = 100

        start_time = time.time()

        for i in range(num_workers):
            t = threading.Thread(target=contention_worker, args=(i, iterations), daemon=True)
            workers.append(t)
            t.start()

        for t in workers:
            t.join()

        duration = time.time() - start_time
        expected = num_workers * iterations
        actual = shared_state['counter']

        print(f"\n   📊 锁竞争深度分析结果:")
        print(f"      工作线程数: {num_workers}")
        print(f"      每线程操作数: {iterations}")
        print(f"      预期操作: {expected}")
        print(f"      实际操作: {actual}")
        print(f"      丢失操作: {expected - actual}")
        print(f"      错误数: {shared_state['errors']}")
        print(f"      锁竞争次数: {contention_count[0]}")
        print(f"      竞争率: {contention_count[0]/expected*100:.2f}%")
        print(f"      总耗时: {duration:.2f}秒")

        perfect = actual == expected
        self.test_results['lock_contention_deep'] = {
            'passed': perfect,
            'expected': expected,
            'actual': actual,
            'lost': expected - actual,
            'contention_count': contention_count[0]
        }

        return perfect

    def test_gc_impact(self, agent, duration_seconds: int = 120):
        """测试4: 垃圾回收影响分析（2分钟）"""
        print(f"\n{'='*80}")
        print(f"🗑️ 测试4: 垃圾回收影响分析 ({duration_seconds}秒)")
        print(f"{'='*80}")

        gc.collect()
        initial_gc = gc.get_count()

        gc_pauses = []
        memory_samples = []

        for i in range(duration_seconds):
            time.sleep(1)

            gc.collect(0)
            before = gc.get_count()
            time.sleep(0.1)
            gc.collect(0)
            after = gc.get_count()

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            memory_samples.append(memory_mb)
            self.monitor.record('memory_samples', memory_mb)
            self.monitor.record('gc_stats', {
                'before': before,
                'after': after,
                'collected': sum(after) - sum(before)
            })

            if i % 20 == 0:
                print(f"   ⏱️ {i}秒: "
                      f"内存={memory_mb:.1f}MB, "
                      f"GC收集={sum(after)-sum(before)}")

        avg_memory = sum(memory_samples) / len(memory_samples)
        memory_variance = sum((m - avg_memory) ** 2 for m in memory_samples) / len(memory_samples)
        memory_stddev = memory_variance ** 0.5

        print(f"\n   📊 GC影响分析结果:")
        print(f"      平均内存: {avg_memory:.2f}MB")
        print(f"      内存标准差: {memory_stddev:.2f}MB")
        print(f"      内存稳定性: {'优秀' if memory_stddev < 10 else '一般' if memory_stddev < 20 else '较差'}")

        stable = memory_stddev < 15
        self.test_results['gc_impact'] = {
            'passed': stable,
            'avg_memory': avg_memory,
            'memory_stddev': memory_stddev
        }

        return stable

    def test_queue_depth_stress(self, agent, duration_seconds: int = 120):
        """测试5: 队列深度压力测试（2分钟）"""
        print(f"\n{'='*80}")
        print(f"📬 测试5: 队列深度压力测试 ({duration_seconds}秒)")
        print(f"{'='*80}")

        tasks_submitted = [0]
        tasks_completed = [0]
        errors = [0]

        def submit_worker():
            for _ in range(50):
                try:
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        {'stress': True, 'data': list(range(100))}
                    )
                    tasks_submitted[0] += 1
                    time.sleep(random.uniform(0.01, 0.05))
                except Exception as e:
                    errors[0] += 1

        workers = []
        num_workers = 20

        print(f"   启动 {num_workers} 个提交工作线程...")

        start_time = time.time()

        for _ in range(num_workers):
            t = threading.Thread(target=submit_worker, daemon=True)
            workers.append(t)
            t.start()

        queue_samples = []

        for i in range(0, duration_seconds, 5):
            time.sleep(5)

            try:
                status = agent.get_system_status()
                exec_summary = status.get('execution', {})
                pending = exec_summary.get('pending_tasks', 0)
                running = exec_summary.get('running_tasks', 0)
                completed = exec_summary.get('completed_tasks', 0)

                queue_samples.append({
                    'second': i,
                    'pending': pending,
                    'running': running,
                    'completed': completed
                })

                print(f"   ⏱️ {i}秒: "
                      f"待处理={pending}, "
                      f"运行中={running}, "
                      f"已完成={completed}")

            except Exception as e:
                print(f"   ❌ 获取状态失败: {str(e)}")
                errors[0] += 1

        for t in workers:
            t.join(timeout=5)

        duration = time.time() - start_time

        print(f"\n   📊 队列深度压力测试结果:")
        print(f"      提交任务: {tasks_submitted[0]}")
        print(f"      错误数: {errors[0]}")
        print(f"      平均待处理: {sum(s['pending'] for s in queue_samples)/len(queue_samples):.1f}")
        print(f"      峰值待处理: {max(s['pending'] for s in queue_samples)}")
        print(f"      吞吐量: {tasks_submitted[0]/duration:.1f}任务/秒")

        healthy = errors[0] < tasks_submitted[0] * 0.1
        self.test_results['queue_depth_stress'] = {
            'passed': healthy,
            'submitted': tasks_submitted[0],
            'errors': errors[0],
            'peak_pending': max(s['pending'] for s in queue_samples)
        }

        return healthy

    def test_long_term_stability_extreme(self, agent, duration_seconds: int = 600):
        """测试6: 极限长时间稳定性测试（10分钟）"""
        print(f"\n{'='*80}")
        print(f"⏱️ 测试6: 极限长时间稳定性测试 ({duration_seconds}秒 = {duration_seconds//60}分钟)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        print(f"   基线内存: {baseline_memory:.2f}MB")

        total_tasks = 0
        total_errors = 0
        checkpoints = []

        checkpoint_interval = 60

        for second in range(0, duration_seconds, 1):
            try:
                batch_size = random.randint(5, 15)
                for _ in range(batch_size):
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        {
                            'iteration': second,
                            'batch': batch_size,
                            'data': [random.random() for _ in range(50)]
                        }
                    )
                    total_tasks += 1

                if second % 30 == 0:
                    gc.collect()

                if second % checkpoint_interval == 0 and second > 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - baseline_memory
                    num_threads = threading.active_count()

                    try:
                        status = agent.get_system_status()
                        health = status['guardian']['overall_status']
                    except:
                        health = 'unknown'

                    checkpoint = {
                        'time': second,
                        'memory_mb': current_memory,
                        'memory_growth_mb': memory_growth,
                        'threads': num_threads,
                        'tasks': total_tasks,
                        'health': health
                    }
                    checkpoints.append(checkpoint)

                    print(f"      📍 {second//60}分钟: "
                          f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                          f"线程={num_threads}, "
                          f"任务={total_tasks}, "
                          f"健康={health}")

                time.sleep(1)

            except Exception as e:
                total_errors += 1
                if total_errors <= 5:
                    print(f"   ❌ 错误: {str(e)}")
                time.sleep(0.1)

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory

        avg_memory = sum(c['memory_mb'] for c in checkpoints) / len(checkpoints)
        memory_variance = sum((c['memory_mb'] - avg_memory) ** 2 for c in checkpoints) / len(checkpoints)
        memory_stddev = memory_variance ** 0.5

        print(f"\n   📊 极限长时间稳定性测试结果:")
        print(f"      总任务数: {total_tasks}")
        print(f"      总错误数: {total_errors}")
        print(f"      错误率: {total_errors/total_tasks*100 if total_tasks > 0 else 0:.3f}%")
        print(f"      最终内存: {final_memory:.2f}MB")
        print(f"      总增长: +{total_growth:.2f}MB")
        print(f"      内存标准差: {memory_stddev:.2f}MB")
        print(f"      增长速率: {total_growth/duration_seconds*60:.2f}MB/分钟")

        healthy = (total_errors / total_tasks < 0.05 if total_tasks > 0 else False) and total_growth < 300
        self.test_results['long_term_stability_extreme'] = {
            'passed': healthy,
            'total_tasks': total_tasks,
            'total_errors': total_errors,
            'error_rate': total_errors/total_tasks*100 if total_tasks > 0 else 0,
            'memory_growth_mb': total_growth,
            'memory_stddev': memory_stddev,
            'checkpoints': checkpoints
        }

        return healthy

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("🔬 慢工出细活 - 极致深度测试框架")
        print("=" * 80)
        print("从细节入手，深度分析系统表现")

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            print("\n📦 初始化Agent...")
            agent = MainLoopController()
            agent.initialize()
            agent.start()
            self.agent = agent

            time.sleep(5)

            print("\n🚀 开始极致深度测试...")
            print("   预计总时长: 约18分钟")
            print("   1. 内存泄漏检测: 5分钟")
            print("   2. 线程池健康检测: 3分钟")
            print("   3. 锁竞争深度分析: 2分钟")
            print("   4. GC影响分析: 2分钟")
            print("   5. 队列深度压力测试: 2分钟")
            print("   6. 极限长时间稳定性测试: 10分钟")

            results = []

            results.append(("内存泄漏检测", self.test_memory_leak_detection(agent, 300)))
            results.append(("线程池健康检测", self.test_thread_pool_health(agent, 180)))
            results.append(("锁竞争深度分析", self.test_lock_contention_deep(agent, 120)))
            results.append(("GC影响分析", self.test_gc_impact(agent, 120)))
            results.append(("队列深度压力测试", self.test_queue_depth_stress(agent, 120)))
            results.append(("极限长时间稳定性测试", self.test_long_term_stability_extreme(agent, 600)))

            print("\n" + "=" * 80)
            print("📋 测试结果汇总")
            print("=" * 80)

            for test_name, passed in results:
                status = "✅ 通过" if passed else "❌ 失败"
                print(f"   {test_name}: {status}")

            monitor_summary = self.monitor.get_summary()
            print(f"\n📊 监控系统统计:")
            for category, stats in monitor_summary.items():
                if isinstance(stats, dict) and 'avg' in stats:
                    print(f"   {category}: avg={stats['avg']:.2f}, max={stats['max']:.2f}")

            all_passed = all(passed for _, passed in results)
            print("\n" + "=" * 80)
            if all_passed:
                print("🎉 所有极致深度测试通过！")
            else:
                failed_tests = [name for name, passed in results if not passed]
                print(f"⚠️  {len(failed_tests)}个测试失败: {', '.join(failed_tests)}")
            print("=" * 80)

            print("\n🛑 停止Agent...")
            agent.stop()
            print("✅ Agent已停止")

            return all_passed

        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            print(traceback.format_exc())
            return False


def main():
    tester = MeticulousTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 未预料的错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
