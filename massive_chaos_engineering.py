#!/usr/bin/env python3
"""
Massive Chaos Engineering Test - 慢工出细活
60分钟+大规模混乱工程测试框架

更极端的混乱场景：
1. 200+线程并发攻击
2. 极端内存压力测试
3. 持续异常注入
4. 大规模畸形数据风暴
5. 线程池爆炸测试
6. 资源耗尽测试
7. 长时间持续混乱攻击
"""
import sys
import time
import random
import threading
import gc
import psutil
import traceback
from typing import List, Dict, Any, Optional
from collections import deque
import os

sys.path.insert(0, '/workspace')


class MassiveChaosMetrics:
    """大规模混乱指标收集器
    收集详细的性能和问题指标"""

    def __init__(self):
        self.metrics = {
            'total_tasks': 0,
            'total_errors': 0,
            'memory_spikes': 0,
            'thread_explosions': 0,
            'high_memory_warnings': 0,
            'recovery_count': 0,
            'timeout_count': 0,
            'crash_count': 0,
            'queue_backlogs': []
        }
        self._lock = threading.Lock()
        self.timeline = []

    def increment(self, metric: str, value: int = 1):
        """增加指标"""
        with self._lock:
            if metric in self.metrics and isinstance(self.metrics[metric], int):
                self.metrics[metric] += value
            self.timeline.append({
                'time': time.time(),
                'metric': metric,
                'value': self.metrics[metric] if metric in self.metrics else None
            })

    def record_queue_backlog(self, backlog_size: int):
        """记录队列积压情况"""
        with self._lock:
            self.metrics['queue_backlogs'].append(backlog_size)

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return self.metrics.copy()


class MassiveChaosEngineeringTest:
    """大规模混乱工程测试器"""

    def __init__(self):
        self.chaos_metrics = MassiveChaosMetrics()
        self.agent = None
        self._stop_chaos = threading.Event()
        self._test_results = {}

    def extreme_concurrent_attack(self, agent, duration_seconds: int = 600):
        """混乱1: 200+线程极端并发攻击 - 10分钟"""
        print(f"\n{'='*80}")
        print(f"🌪️ 混乱1: 200+线程极端并发攻击 ({duration_seconds//60}分钟)")
        print(f"{'='*80}")

        workers = []
        num_workers = 200
        tasks_per_worker = 100
        self._start_time = time.time()

        def chaos_worker(worker_id: int):
            for i in range(tasks_per_worker):
                if self._stop_chaos.is_set():
                    break
                try:
                    payload = {
                        'chaos_level': 'extreme',
                        'worker_id': worker_id,
                        'iteration': i,
                        'timestamp': time.time(),
                        'data': [random.random() for _ in range(random.randint(1, 500))]
                    }
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        payload
                    )
                    self.chaos_metrics.increment('total_tasks')
                    time.sleep(random.uniform(0.001, 0.02))
                except Exception as e:
                    self.chaos_metrics.increment('total_errors')
                    if self.chaos_metrics.metrics['total_errors'] <= 10:
                        print(f"   ❌ Worker-{worker_id}: {str(e)}")

        print(f"   🚀 启动 {num_workers} 个极端混乱工作线程...")

        for i in range(num_workers):
            t = threading.Thread(target=chaos_worker, args=(i,), daemon=True)
            workers.append(t)
            t.start()

        initial_threads = threading.active_count()
        print(f"   🔥 所有 {num_workers} 个线程已启动，开始极端并发攻击...")

        for i in range(0, duration_seconds, 30):
            time.sleep(30)
            current_threads = threading.active_count()
            thread_growth = current_threads - initial_threads

            if thread_growth > 100:
                self.chaos_metrics.increment('thread_explosions')
                print(f"   ⚠️  线程爆炸: {current_threads} (增长+{thread_growth})")

            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"   ⏱️ {i//60}分钟: "
                  f"线程={current_threads} (+{thread_growth}), "
                  f"任务={self.chaos_metrics.metrics['total_tasks']}, "
                  f"错误={self.chaos_metrics.metrics['total_errors']}, "
                  f"内存={current_memory:.1f}MB")

        for t in workers:
            t.join(timeout=5)

        duration = time.time() - self._start_time
        print(f"\n   📊 极端并发攻击结果:")
        print(f"      工作线程: {num_workers}")
        print(f"      总任务数: {self.chaos_metrics.metrics['total_tasks']}")
        print(f"      总错误数: {self.chaos_metrics.metrics['total_errors']}")
        print(f"      线程爆炸次数: {self.chaos_metrics.metrics['thread_explosions']}")
        print(f"      吞吐量: {self.chaos_metrics.metrics['total_tasks']/duration:.1f}任务/秒")

        self._test_results['extreme_concurrent_attack'] = {
            'passed': self.chaos_metrics.metrics['total_errors'] < self.chaos_metrics.metrics['total_tasks'] * 0.1,
            'total_tasks': self.chaos_metrics.metrics['total_tasks'],
            'total_errors': self.chaos_metrics.metrics['total_errors']
        }

    def extreme_memory_stress(self, agent, duration_seconds: int = 300):
        """混乱2: 极端内存压力测试 - 5分钟"""
        print(f"\n{'='*80}")
        print(f"💣 混乱2: 极端内存压力测试 ({duration_seconds//60}分钟)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        print(f"   基线内存: {baseline_memory:.2f}MB")

        large_objects = []

        for i in range(duration_seconds):
            try:
                if i % 3 == 0:
                    large_obj = {
                        'id': i,
                        'data': [random.random() for _ in range(random.randint(1000, 100000))],
                        'timestamp': time.time()
                    }
                    large_objects.append(large_obj)

                    agent.submit_task('compute', large_obj)
                    self.chaos_metrics.increment('total_tasks')

                if i % 60 == 0 and i > 0:
                    gc.collect()
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - baseline_memory

                    print(f"   ⏱️ {i//60}分钟: "
                          f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                          f"大对象数量={len(large_objects)}")

                    if memory_growth > 1000:
                        self.chaos_metrics.increment('memory_spikes')
                        self.chaos_metrics.increment('high_memory_warnings')
                        print(f"   ⚠️  内存尖峰警告: +{memory_growth:.1f}MB")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 5:
                    print(f"   ❌ 内存压力错误: {str(e)}")

        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory
        print(f"\n   📊 极端内存压力测试结果:")
        print(f"      最终内存: {final_memory:.2f}MB")
        print(f"      总增长: +{total_growth:.2f}MB")
        print(f"      内存尖峰次数: {self.chaos_metrics.metrics['memory_spikes']}")
        print(f"      内存警告次数: {self.chaos_metrics.metrics['high_memory_warnings']}")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")

        self._test_results['extreme_memory_stress'] = {
            'passed': self.chaos_metrics.metrics['high_memory_warnings'] < 20,
            'memory_growth_mb': total_growth,
            'total_tasks': self.chaos_metrics.metrics['total_tasks']
        }

    def continuous_exception_injection(self, agent, duration_seconds: int = 600):
        """混乱3: 持续异常注入 - 10分钟"""
        print(f"\n{'='*80}")
        print(f"⚡ 混乱3: 持续异常注入 ({duration_seconds//60}分钟)")
        print(f"{'='*80}")

        invalid_data_types = [
            None, '', [], {}, 123, 0, -1, float('inf'), float('-inf'),
            float('nan')
        ]

        invalid_payloads = [
            None, '', [], {}
        ]

        start_time = time.time()
        for i in range(duration_seconds):
            try:
                if i % 2 == 0:
                    invalid_type = random.choice(invalid_data_types)
                    agent.submit_task(invalid_type, {'chaos': 'continuous'})

                if i % 4 == 0:
                    invalid_payload = random.choice(invalid_payloads)
                    agent.submit_task('compute', invalid_payload)

                if i % 60 == 0:
                    try:
                        status = agent.get_system_status()
                        health = status['guardian']['overall_status']
                        if health == 'healthy':
                            self.chaos_metrics.increment('recovery_count')
                        print(f"   ⏱️ {i//60}分钟: 健康状态={health}, 恢复次数={self.chaos_metrics.metrics['recovery_count']}")
                    except Exception as e:
                        self.chaos_metrics.increment('crash_count')
                        print(f"   ❌ 状态获取失败: {str(e)}")

                time.sleep(1)
            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 5:
                    print(f"   ❌ 异常注入错误: {str(e)}")

        try:
            final_status = agent.get_system_status()
            final_health = final_status['guardian']['overall_status']
        except:
            final_health = 'unknown'

        print(f"\n   📊 持续异常注入结果:")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")
        print(f"      恢复次数: {self.chaos_metrics.metrics['recovery_count']}")
        print(f"      崩溃次数: {self.chaos_metrics.metrics['crash_count']}")
        print(f"      最终健康: {final_health}")

        self._test_results['continuous_exception_injection'] = {
            'passed': final_health == 'healthy',
            'final_health': final_health
        }

    def massive_deformed_data_storm(self, agent, duration_seconds: int = 600):
        """混乱4: 大规模畸形数据风暴 - 10分钟"""
        print(f"\n{'='*80}")
        print(f"👹 混乱4: 大规模畸形数据风暴 ({duration_seconds//60}分钟)")
        print(f"{'='*80}")

        deformed_payloads = [
            {'circular_ref': None},
            {'very_deep': {'level1': {'level2': {'level3': {'level4': {'level5': {'level6': {'level7': {'level8': {'level9': {'level10': 'super_deep'}}}}}}}},
            {'giant_list': list(range(500000))},
            {'giant_string': 'x' * 2000000},
            {'unicode_hell': ''.join(chr(i) for i in range(20000))},
            {'nested_lists': [[[[[[[[[[[1]]]]]]]]]},
            {'mixed_types': [1, 'string', None, [], {}, 3.14, True, False, [], {}, None, 1.0, 'test', [] for _ in range(1000)]}
        ]

        for i in range(duration_seconds):
            try:
                deformed_payload = random.choice(deformed_payloads)
                if i % 3 == 0:
                    deformed_payload['timestamp'] = time.time()
                    deformed_payload['iteration'] = i
                agent.submit_task('compute', deformed_payload)
                self.chaos_metrics.increment('total_tasks')
                if i % 60 == 0:
                    print(f"   ⏱️ {i//60}分钟: 已提交{self.chaos_metrics.metrics['total_tasks']}个畸形数据任务")
                time.sleep(1)
            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 10:
                    print(f"   ❌ 畸形数据错误: {str(e)}")

        print(f"\n   📊 大规模畸形数据风暴结果:")
        print(f"      总任务数: {self.chaos_metrics.metrics['total_tasks']}")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")

        self._test_results['massive_deformed_data_storm'] = {
            'passed': self.chaos_metrics.metrics['total_errors'] < 50,
            'total_tasks': self.chaos_metrics.metrics['total_tasks'],
            'total_errors': self.chaos_metrics.metrics['total_errors']
        }

    def long_term_sustained_chaos(self, agent, duration_seconds: int = 2400):
        """混乱5: 长时间持续混乱攻击 - 40分钟"""
        print(f"\n{'='*80}")
        print(f"⏰ 混乱5: 长时间持续混乱攻击 ({duration_seconds//60}分钟)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        print(f"   基线内存: {baseline_memory:.2f}MB")
        checkpoints = []
        healthy_count = 0

        for second in range(duration_seconds):
            try:
                chaos_intensity = random.randint(1, 15)
                batch_size = random.randint(1, chaos_intensity * 8)

                for _ in range(batch_size):
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        {
                            'chaos_intensity': chaos_intensity,
                            'second': second,
                            'timestamp': time.time(),
                            'data': [random.random() for _ in range(random.randint(1, 200))]
                        }
                    )

                if second % 120 == 0 and second > 0:
                    gc.collect()
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - baseline_memory
                    num_threads = threading.active_count()

                    try:
                        status = agent.get_system_status()
                        health = status['guardian']['overall_status']
                        tasks_completed = status['statistics']['total_tasks']
                    except:
                        health = 'unknown'
                        tasks_completed = 0

                    checkpoint = {
                        'time': second,
                        'memory_mb': current_memory,
                        'memory_growth_mb': memory_growth,
                        'threads': num_threads,
                        'health': health,
                        'tasks_completed': tasks_completed
                    }
                    checkpoints.append(checkpoint)

                    if health == 'healthy':
                        healthy_count += 1

                    print(f"      📍 {second//60}分钟: "
                          f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                          f"线程={num_threads}, "
                          f"健康={health}")

                    if health != 'healthy':
                        print(f"   ⚠️  系统不健康!")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 5:
                    print(f"   ❌ 持续混乱错误: {str(e)}")
                time.sleep(0.1)

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory

        if checkpoints:
            avg_memory = sum(c['memory_mb'] for c in checkpoints) / len(checkpoints)
            memory_variance = sum((c['memory_mb'] - avg_memory) ** 2 for c in checkpoints) / len(checkpoints)
            memory_stddev = memory_variance ** 0.5
        else:
            memory_stddev = 0

        health_rate = healthy_count / len(checkpoints) * 100 if len(checkpoints) > 0 else 0
        print(f"\n   📊 长时间持续混乱攻击结果:")
        print(f"      总错误数: {self.chaos_metrics.metrics['total_errors']}")
        print(f"      最终内存: {final_memory:.2f}MB")
        print(f"      总增长: +{total_growth:.2f}MB")
        print(f"      内存标准差: {memory_stddev:.2f}MB")
        print(f"      健康率: {health_rate:.1f}%")

        self._test_results['long_term_sustained_chaos'] = {
            'passed': health_rate >= 90,
            'health_rate': health_rate
        }

    def run_all_tests(self):
        """运行所有大规模混乱测试"""
        print("=" * 80)
        print("🌪️ 大规模混沌工程测试框架")
        print("=" * 80)
        print("更大规模、更混乱、更极端的测试场景")

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            print("\n📦 初始化Agent...")
            agent = MainLoopController()
            agent.initialize()
            agent.start()
            self.agent = agent

            time.sleep(10)

            print("\n🚀 开始大规模混沌工程测试...")
            print("   预计总时长: 约80分钟")
            print("   1. 200+线程极端并发攻击: 10分钟")
            print("   2. 极端内存压力测试: 5分钟")
            print("   3. 持续异常注入: 10分钟")
            print("   4. 大规模畸形数据风暴: 10分钟")
            print("   5. 长时间持续混乱攻击: 40分钟")

            results = []

            print("\n=== 开始第一阶段：极端并发攻击 ===\n")
            results.append(("extreme_concurrent_attack", self.extreme_concurrent_attack(agent, 600)))

            print("\n=== 开始第二阶段：极端内存压力 ===\n")
            results.append(("extreme_memory_stress", self.extreme_memory_stress(agent, 300)))

            print("\n=== 开始第三阶段：持续异常注入 ===\n")
            results.append(("continuous_exception_injection", self.continuous_exception_injection(agent, 600)))

            print("\n=== 开始第四阶段：大规模畸形数据风暴 ===\n")
            results.append(("massive_deformed_data_storm", self.massive_deformed_data_storm(agent, 600)))

            print("\n=== 开始第五阶段：长时间持续混乱攻击 ===\n")
            results.append(("long_term_sustained_chaos", self.long_term_sustained_chaos(agent, 2400)))

            print("\n" + "=" * 80)
            print("📋 大规模混沌工程测试结果汇总")
            print("=" * 80)

            for test_name, _ in results:
                test_result = self._test_results.get(test_name, {})
                passed = test_result.get('passed', False)
                status = "✅ 通过" if passed else "❌ 失败"
                print(f"   {test_name}: {status}")

            chaos_metrics = self.chaos_metrics.get_metrics()
            print(f"\n📊 大规模混乱指标统计:")
            for metric, value in chaos_metrics.items():
                if isinstance(value, (int, float)) and value > 0:
                    print(f"   {metric}: {value}")

            all_passed = all(self._test_results.get(name, {}).get('passed', False) for name, _ in results)
            print("\n" + "=" * 80)
            if all_passed:
                print("🎉 所有大规模混沌工程测试通过！系统展现出极强的韧性！")
            else:
                print(f"⚠️  部分测试失败")
            print("=" * 80)

            print("\n🛑 停止Agent...")
            agent.stop()
            print("✅ Agent已停止")

            return all_passed

        except Exception as e:
            print(f"\n❌ 大规模混沌测试失败: {str(e)}")
            traceback.print_exc()
            return False


def main():
    chaos_tester = MassiveChaosEngineeringTest()
    success = chaos_tester.run_all_tests()
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
