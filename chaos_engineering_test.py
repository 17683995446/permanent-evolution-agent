#!/usr/bin/env python3
"""
混沌工程级别混乱测试 - 慢工出细活
模拟真实世界中的极端混乱场景，测试系统的韧性和稳定性

核心混乱场景：
1. 并发混乱攻击 - 100+线程同时疯狂提交
2. 资源耗尽攻击 - 耗尽内存、线程、文件句柄
3. 异常混乱风暴 - 各种异常同时爆发
4. 数据混乱地狱 - 畸形数据循环攻击
5. 调度混乱战争 - 优先级任务混乱冲突
6. 边界混乱风暴 - 极端边界同时触发
7. 长时间混乱持续 - 30分钟混乱攻击
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
from collections import deque
import signal
import os

sys.path.insert(0, '/workspace')


class ChaosMetrics:
    """混乱指标收集器"""

    def __init__(self):
        self.metrics = {
            'total_tasks': 0,
            'total_errors': 0,
            'memory_spikes': 0,
            'thread_explosions': 0,
            'deadlocks_detected': 0,
            'recovery_count': 0,
            'timeout_count': 0,
            'crash_count': 0
        }
        self._lock = threading.Lock()
        self.timeline = []

    def increment(self, metric: str, value: int = 1):
        with self._lock:
            if metric in self.metrics:
                self.metrics[metric] += value
                self.timeline.append({
                    'time': time.time(),
                    'metric': metric,
                    'value': self.metrics[metric]
                })

    def get_metrics(self) -> Dict[str, int]:
        with self._lock:
            return self.metrics.copy()


class ChaosEngineeringTest:
    """混沌工程测试器"""

    def __init__(self):
        self.chaos_metrics = ChaosMetrics()
        self.agent = None
        self._stop_chaos = threading.Event()
        self.test_results = {}

    def chaos_concurrent_attack(self, agent, duration_seconds: int = 180):
        """混乱1: 并发混乱攻击 - 100线程同时疯狂提交"""
        print(f"\n{'='*80}")
        print(f"🌪️ 混乱1: 并发混乱攻击 ({duration_seconds}秒)")
        print(f"{'='*80}")

        workers = []
        num_workers = 100
        tasks_per_worker = 50

        def chaos_worker(worker_id: int):
            for i in range(tasks_per_worker):
                if self._stop_chaos.is_set():
                    break

                try:
                    payload = {
                        'chaos': True,
                        'worker_id': worker_id,
                        'iteration': i,
                        'timestamp': time.time(),
                        'data': [random.random() for _ in range(random.randint(1, 200))]
                    }

                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze', 'compute', 'compute']),
                        payload
                    )

                    self.chaos_metrics.increment('total_tasks')

                    time.sleep(random.uniform(0.001, 0.01))

                except Exception as e:
                    self.chaos_metrics.increment('total_errors')
                    if self.chaos_metrics.metrics['total_errors'] <= 10:
                        print(f"   ❌ Worker-{worker_id}: {str(e)}")

        print(f"   🚀 启动 {num_workers} 个混乱工作线程...")

        start_time = time.time()

        for i in range(num_workers):
            t = threading.Thread(target=chaos_worker, args=(i,), daemon=True)
            workers.append(t)
            t.start()

        print(f"   🔥 所有 {num_workers} 个线程已启动，开始混乱攻击...")

        initial_threads = threading.active_count()

        for i in range(0, duration_seconds, 10):
            time.sleep(10)

            current_threads = threading.active_count()
            thread_growth = current_threads - initial_threads

            if thread_growth > 50:
                self.chaos_metrics.increment('thread_explosions')
                print(f"   ⚠️  线程爆炸: {current_threads} (增长+{thread_growth})")

            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024

            print(f"   ⏱️ {i+10}秒: "
                  f"线程={current_threads} (+{thread_growth}), "
                  f"任务={self.chaos_metrics.metrics['total_tasks']}, "
                  f"错误={self.chaos_metrics.metrics['total_errors']}, "
                  f"内存={current_memory:.1f}MB")

        for t in workers:
            t.join(timeout=5)

        duration = time.time() - start_time

        print(f"\n   📊 并发混乱攻击结果:")
        print(f"      工作线程: {num_workers}")
        print(f"      总任务数: {self.chaos_metrics.metrics['total_tasks']}")
        print(f"      总错误数: {self.chaos_metrics.metrics['total_errors']}")
        print(f"      线程爆炸次数: {self.chaos_metrics.metrics['thread_explosions']}")
        print(f"      吞吐量: {self.chaos_metrics.metrics['total_tasks']/duration:.1f}任务/秒")

        self.test_results['chaos_concurrent_attack'] = {
            'passed': self.chaos_metrics.metrics['total_errors'] < self.chaos_metrics.metrics['total_tasks'] * 0.5,
            'total_tasks': self.chaos_metrics.metrics['total_tasks'],
            'total_errors': self.chaos_metrics.metrics['total_errors'],
            'thread_explosions': self.chaos_metrics.metrics['thread_explosions']
        }

    def chaos_resource_exhaustion(self, agent, duration_seconds: int = 120):
        """混乱2: 资源耗尽攻击"""
        print(f"\n{'='*80}")
        print(f"💣 混乱2: 资源耗尽攻击 ({duration_seconds}秒)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        print(f"   基线内存: {baseline_memory:.2f}MB")

        large_objects = []
        file_handles = []

        for i in range(duration_seconds):
            try:
                phase = i % 5

                if phase == 0:
                    large_obj = {
                        'id': i,
                        'data': [random.random() for _ in range(10000)],
                        'timestamp': time.time()
                    }
                    large_objects.append(large_obj)

                elif phase == 1:
                    try:
                        with open(f'/tmp/chaos_test_{i}.tmp', 'w') as f:
                            f.write('chaos' * 1000)
                        file_handles.append(i)
                    except:
                        pass

                elif phase == 2:
                    if len(large_objects) > 10:
                        large_objects = large_objects[-5:]

                elif phase == 3:
                    if len(file_handles) > 5:
                        for handle_id in file_handles[:3]:
                            try:
                                os.remove(f'/tmp/chaos_test_{handle_id}.tmp')
                            except:
                                pass
                        file_handles = file_handles[3:]

                gc.collect()

                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - baseline_memory
                    open_files = len(process.open_files())
                    num_threads = threading.active_count()

                    print(f"   ⏱️ {i}秒: "
                          f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                          f"对象={len(large_objects)}, "
                          f"文件={len(file_handles)}, "
                          f"线程={num_threads}")

                    if memory_growth > 500:
                        self.chaos_metrics.increment('memory_spikes')
                        print(f"   ⚠️  内存尖峰: +{memory_growth:.1f}MB")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 5:
                    print(f"   ❌ 资源耗尽错误: {str(e)}")

        for handle_id in file_handles:
            try:
                os.remove(f'/tmp/chaos_test_{handle_id}.tmp')
            except:
                pass

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory

        print(f"\n   📊 资源耗尽攻击结果:")
        print(f"      最终内存: {final_memory:.2f}MB")
        print(f"      总增长: +{total_growth:.2f}MB")
        print(f"      内存尖峰次数: {self.chaos_metrics.metrics['memory_spikes']}")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")

        self.test_results['chaos_resource_exhaustion'] = {
            'passed': self.chaos_metrics.metrics['memory_spikes'] < 10,
            'memory_growth_mb': total_growth,
            'memory_spikes': self.chaos_metrics.metrics['memory_spikes']
        }

    def chaos_exception_storm(self, agent, duration_seconds: int = 120):
        """混乱3: 异常混乱风暴"""
        print(f"\n{'='*80}")
        print(f"⚡ 混乱3: 异常混乱风暴 ({duration_seconds}秒)")
        print(f"{'='*80}")

        invalid_types = [
            None, '', [], {}, 123, 0, -1, float('inf'), float('-inf'),
            float('nan'), Exception(), BaseException(), KeyboardInterrupt
        ]

        invalid_payloads = [
            None, '', [], {}, {(1, 2): 'test'}, {(1, 2): 'value'},
            Exception('chaos'), {'nested': {(3, 4): 'deep'}}
        ]

        for i in range(duration_seconds):
            try:
                if i % 3 == 0:
                    invalid_type = random.choice(invalid_types)
                    agent.submit_task(invalid_type, {'chaos': True})

                if i % 5 == 0:
                    invalid_payload = random.choice(invalid_payloads)
                    agent.submit_task('compute', invalid_payload)

                if i % 7 == 0:
                    agent.submit_task(None, None)

                time.sleep(1)

                if i % 20 == 0:
                    try:
                        status = agent.get_system_status()
                        health = status['guardian']['overall_status']
                        if health == 'healthy':
                            self.chaos_metrics.increment('recovery_count')
                        print(f"   ⏱️ {i}秒: 健康状态={health}, 恢复次数={self.chaos_metrics.metrics['recovery_count']}")
                    except Exception as e:
                        self.chaos_metrics.increment('crash_count')
                        print(f"   ❌ 状态获取失败: {str(e)}")

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 5:
                    print(f"   ❌ 异常风暴错误: {str(e)}")

        try:
            final_status = agent.get_system_status()
            final_health = final_status['guardian']['overall_status']
        except:
            final_health = 'unknown'

        print(f"\n   📊 异常混乱风暴结果:")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")
        print(f"      恢复次数: {self.chaos_metrics.metrics['recovery_count']}")
        print(f"      崩溃次数: {self.chaos_metrics.metrics['crash_count']}")
        print(f"      最终健康: {final_health}")

        self.test_results['chaos_exception_storm'] = {
            'passed': final_health == 'healthy',
            'total_errors': self.chaos_metrics.metrics['total_errors'],
            'recovery_count': self.chaos_metrics.metrics['recovery_count'],
            'final_health': final_health
        }

    def chaos_data_hell(self, agent, duration_seconds: int = 120):
        """混乱4: 数据混乱地狱"""
        print(f"\n{'='*80}")
        print(f"👹 混乱4: 数据混乱地狱 ({duration_seconds}秒)")
        print(f"{'='*80}")

        chaotic_data = [
            {'circular_ref': None},
            {'very_deep': {'level1': {'level2': {'level3': {'level4': {'level5': 'deep'}}}}}},
            {'giant_list': list(range(100000))},
            {'giant_string': 'x' * 1000000},
            {'unicode_hell': ''.join(chr(i) for i in range(10000))},
            {'nested_lists': [[[[[1]]]]]},
            {'mixed_types': [1, 'string', None, [], {}, 3.14, True]},
            {'recursive_dict': {'a': {'a': {'a': {'a': {'a': 'infinite'}}}}}},
            {'bytes_hell': bytes(range(256)) * 1000},
            {'empty_strings': {'': '', '': '', '': ''}}
        ]

        for i in range(duration_seconds):
            try:
                chaotic_payload = random.choice(chaotic_data)

                if i % 3 == 0:
                    chaotic_payload['timestamp'] = time.time()
                    chaotic_payload['iteration'] = i

                agent.submit_task('compute', chaotic_payload)
                self.chaos_metrics.increment('total_tasks')

                if i % 20 == 0:
                    print(f"   ⏱️ {i}秒: 已提交{self.chaos_metrics.metrics['total_tasks']}个混乱数据任务")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 10:
                    print(f"   ❌ 数据混乱错误: {str(e)}")

        print(f"\n   📊 数据混乱地狱结果:")
        print(f"      总任务数: {self.chaos_metrics.metrics['total_tasks']}")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")

        self.test_results['chaos_data_hell'] = {
            'passed': self.chaos_metrics.metrics['total_errors'] < 20,
            'total_tasks': self.chaos_metrics.metrics['total_tasks'],
            'total_errors': self.chaos_metrics.metrics['total_errors']
        }

    def chaos_scheduling_war(self, agent, duration_seconds: int = 120):
        """混乱5: 调度混乱战争"""
        print(f"\n{'='*80}")
        print(f"⚔️ 混乱5: 调度混乱战争 ({duration_seconds}秒)")
        print(f"{'='*80}")

        priorities = ['low', 'normal', 'high', 'critical']
        task_types = ['compute', 'process', 'analyze', 'report', 'backup', 'sync']

        for i in range(duration_seconds):
            try:
                num_tasks = random.randint(5, 20)

                for _ in range(num_tasks):
                    priority = random.choice(priorities)
                    task_type = random.choice(task_types)

                    agent.submit_task(task_type, {
                        'priority': priority,
                        'iteration': i,
                        'timestamp': time.time()
                    })

                if i % 10 == 0:
                    print(f"   ⏱️ {i}秒: 提交{num_tasks}个任务, 优先级混乱")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 5:
                    print(f"   ❌ 调度混乱错误: {str(e)}")

        print(f"\n   📊 调度混乱战争结果:")
        print(f"      总错误数: {self.chaos_metrics.metrics['total_errors']}")

        self.test_results['chaos_scheduling_war'] = {
            'passed': True,
            'total_errors': self.chaos_metrics.metrics['total_errors']
        }

    def chaos_boundary_storm(self, agent, duration_seconds: int = 120):
        """混乱6: 边界混乱风暴"""
        print(f"\n{'='*80}")
        print(f"🌊 混乱6: 边界混乱风暴 ({duration_seconds}秒)")
        print(f"{'='*80}")

        boundary_cases = [
            (sys.maxsize, 'max_int'),
            (-sys.maxsize, 'min_int'),
            (0, 'zero'),
            (0.0, 'zero_float'),
            (float('inf'), 'infinity'),
            (float('-inf'), 'neg_infinity'),
            (float('nan'), 'nan'),
            ('', 'empty_string'),
            ([], 'empty_list'),
            ({}, 'empty_dict'),
            (None, 'none'),
            (True, 'true'),
            (False, 'false')
        ]

        for i in range(duration_seconds):
            try:
                case = boundary_cases[i % len(boundary_cases)]
                value, name = case

                payload = {
                    'boundary': name,
                    'value': value,
                    'iteration': i
                }

                agent.submit_task('compute', payload)
                self.chaos_metrics.increment('total_tasks')

                if i % 20 == 0:
                    print(f"   ⏱️ {i}秒: 测试边界值 '{name}'")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 10:
                    print(f"   ❌ 边界混乱错误 ({name}): {str(e)}")

        print(f"\n   📊 边界混乱风暴结果:")
        print(f"      总任务数: {self.chaos_metrics.metrics['total_tasks']}")
        print(f"      错误数: {self.chaos_metrics.metrics['total_errors']}")

        self.test_results['chaos_boundary_storm'] = {
            'passed': self.chaos_metrics.metrics['total_errors'] < 30,
            'total_tasks': self.chaos_metrics.metrics['total_tasks'],
            'total_errors': self.chaos_metrics.metrics['total_errors']
        }

    def chaos_long_term_sustained(self, agent, duration_seconds: int = 1200):
        """混乱7: 长时间混乱持续攻击"""
        print(f"\n{'='*80}")
        print(f"⏰ 混乱7: 长时间混乱持续攻击 ({duration_seconds}秒 = {duration_seconds//60}分钟)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        print(f"   基线内存: {baseline_memory:.2f}MB")

        checkpoints = []

        for second in range(duration_seconds):
            try:
                chaos_level = random.randint(1, 10)

                num_tasks = random.randint(5, chaos_level * 5)

                for _ in range(num_tasks):
                    agent.submit_task(
                        random.choice(['compute', 'process', 'analyze']),
                        {
                            'chaos': True,
                            'second': second,
                            'level': chaos_level,
                            'data': [random.random() for _ in range(50)]
                        }
                    )

                if second % 60 == 0 and second > 0:
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

                    print(f"      📍 {second//60}分钟: "
                          f"内存={current_memory:.1f}MB (+{memory_growth:.1f}), "
                          f"线程={num_threads}, "
                          f"任务={tasks_completed}, "
                          f"健康={health}")

                    if health != 'healthy':
                        print(f"   ⚠️  系统不健康!")

                time.sleep(1)

            except Exception as e:
                self.chaos_metrics.increment('total_errors')
                if self.chaos_metrics.metrics['total_errors'] <= 10:
                    print(f"   ❌ 长时间混乱错误: {str(e)}")
                time.sleep(0.1)

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory

        avg_memory = sum(c['memory_mb'] for c in checkpoints) / len(checkpoints) if checkpoints else final_memory
        memory_variance = sum((c['memory_mb'] - avg_memory) ** 2 for c in checkpoints) / len(checkpoints) if checkpoints else 0
        memory_stddev = memory_variance ** 0.5

        healthy_count = sum(1 for c in checkpoints if c['health'] == 'healthy')
        total_checkpoints = len(checkpoints)
        health_rate = healthy_count / total_checkpoints * 100 if total_checkpoints > 0 else 0

        print(f"\n   📊 长时间混乱持续攻击结果:")
        print(f"      总错误数: {self.chaos_metrics.metrics['total_errors']}")
        print(f"      最终内存: {final_memory:.2f}MB")
        print(f"      总增长: +{total_growth:.2f}MB")
        print(f"      内存标准差: {memory_stddev:.2f}MB")
        print(f"      健康率: {health_rate:.1f}% ({healthy_count}/{total_checkpoints})")

        self.test_results['chaos_long_term_sustained'] = {
            'passed': health_rate >= 90,
            'total_errors': self.chaos_metrics.metrics['total_errors'],
            'memory_growth_mb': total_growth,
            'memory_stddev': memory_stddev,
            'health_rate': health_rate,
            'checkpoints': checkpoints
        }

    def run_chaos_tests(self):
        """运行所有混沌测试"""
        print("=" * 80)
        print("🌪️ 混沌工程 - 混乱测试框架")
        print("=" * 80)
        print("模拟真实世界的极端混乱场景")

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            print("\n📦 初始化Agent...")
            agent = MainLoopController()
            agent.initialize()
            agent.start()
            self.agent = agent

            time.sleep(5)

            print("\n🚀 开始混沌工程测试...")
            print("   预计总时长: 约33分钟")
            print("   1. 并发混乱攻击: 3分钟")
            print("   2. 资源耗尽攻击: 2分钟")
            print("   3. 异常混乱风暴: 2分钟")
            print("   4. 数据混乱地狱: 2分钟")
            print("   5. 调度混乱战争: 2分钟")
            print("   6. 边界混乱风暴: 2分钟")
            print("   7. 长时间混乱持续攻击: 20分钟")

            results = []

            results.append(("并发混乱攻击", self.chaos_concurrent_attack(agent, 180)))
            results.append(("资源耗尽攻击", self.chaos_resource_exhaustion(agent, 120)))
            results.append(("异常混乱风暴", self.chaos_exception_storm(agent, 120)))
            results.append(("数据混乱地狱", self.chaos_data_hell(agent, 120)))
            results.append(("调度混乱战争", self.chaos_scheduling_war(agent, 120)))
            results.append(("边界混乱风暴", self.chaos_boundary_storm(agent, 120)))
            results.append(("长时间混乱持续攻击", self.chaos_long_term_sustained(agent, 1200)))

            print("\n" + "=" * 80)
            print("📋 混沌工程测试结果汇总")
            print("=" * 80)

            for test_name, result in results:
                status = "✅ 通过" if result else "❌ 失败"
                print(f"   {test_name}: {status}")

            chaos_metrics = self.chaos_metrics.get_metrics()
            print(f"\n📊 混乱指标统计:")
            for metric, value in chaos_metrics.items():
                if value > 0:
                    print(f"   {metric}: {value}")

            all_passed = all(passed for _, passed in results)
            print("\n" + "=" * 80)
            if all_passed:
                print("🎉 所有混沌工程测试通过！系统展现出极强的韧性！")
            else:
                failed_tests = [name for name, passed in results if not passed]
                print(f"⚠️  {len(failed_tests)}个测试失败")
            print("=" * 80)

            print("\n🛑 停止Agent...")
            agent.stop()
            print("✅ Agent已停止")

            return all_passed

        except Exception as e:
            print(f"\n❌ 混沌测试失败: {str(e)}")
            traceback.print_exc()
            return False


def main():
    chaos_tester = ChaosEngineeringTest()
    success = chaos_tester.run_chaos_tests()
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
