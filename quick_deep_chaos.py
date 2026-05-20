#!/usr/bin/env python3
"""
快速深度混乱测试 - 慢工出细活
深度但更快的测试，用于快速发现问题
"""
import sys
import time
import random
import threading
import gc
import psutil
import traceback
from typing import List, Dict, Any

sys.path.insert(0, '/workspace')


class QuickChaosTest:
    """快速深度混乱测试器"""

    def __init__(self):
        self.issues_found = []
        self.agent = None

    def test_task_submission_boundary(self, agent):
        """测试1: 任务提交边界条件 - 极端输入"""
        print(f"\n{'='*80}")
        print(f"🌪️ 测试1: 任务提交边界条件 - 极端输入")
        print(f"{'='*80}")

        boundary_tests = [
            ("None任务类型", None, {'data': 'test'}),
            ("空字符串任务类型", '', {'data': 'test'}),
            ("列表作为任务类型", ['invalid'], {'data': 'test'}),
            ("字典作为任务类型", {'invalid': 'type'}, {'data': 'test'}),
            ("超大字符串任务类型", 'x' * 10000, {'data': 'test'}),
            ("None载荷", 'compute', None),
            ("空字符串载荷", 'compute', ''),
            ("超大载荷", 'compute', {'large': 'x' * 500000}),
            ("巨型列表载荷", 'compute', list(range(100000))),
            ("极端数值", 'compute', {'max': sys.maxsize, 'min': -sys.maxsize}),
            ("浮点无穷大", 'compute', {'inf': float('inf'), 'neg_inf': float('-inf')}),
            ("NaN值", 'compute', {'nan': float('nan')}),
        ]

        errors = 0
        for name, task_type, payload in boundary_tests:
            try:
                agent.submit_task(task_type, payload)
                print(f"   ✅ {name}: 提交成功")
            except Exception as e:
                errors += 1
                self.issues_found.append(f"边界测试失败 - {name}: {str(e)}")
                print(f"   ❌ {name}: {str(e)}")

        print(f"\n   📊 边界条件测试结果: {len(boundary_tests)-errors}/{len(boundary_tests)} 成功")
        return errors == 0

    def test_high_concurrency(self, agent, duration_seconds: int = 60):
        """测试2: 高并发压力 - 100线程"""
        print(f"\n{'='*80}")
        print(f"⚡ 测试2: 高并发压力 - 100线程 ({duration_seconds}秒)")
        print(f"{'='*80}")

        workers = []
        errors = 0
        total_tasks = [0]
        completed_tasks = [0]

        def worker(worker_id):
            for i in range(50):
                try:
                    payload = {'worker_id': worker_id, 'iteration': i}
                    agent.submit_task('compute', payload)
                    total_tasks[0] += 1
                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        print(f"   ❌ Worker {worker_id}: {str(e)}")

        print(f"   启动100个工作线程...")
        for i in range(100):
            t = threading.Thread(target=worker, args=(i,), daemon=True)
            workers.append(t)
            t.start()

        start_time = time.time()
        initial_threads = threading.active_count()
        print(f"   初始线程数: {initial_threads}")

        for i in range(duration_seconds):
            time.sleep(1)
            current_threads = threading.active_count()
            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024

            if (i + 1) % 10 == 0:
                print(f"   ⏱️ {i+1}秒: 线程={current_threads}, 任务={total_tasks[0]}, 内存={current_memory:.1f}MB")

        for t in workers:
            t.join(timeout=5)

        print(f"\n   📊 高并发测试结果: 总任务={total_tasks[0]}, 错误={errors}")
        return errors < total_tasks[0] * 0.1

    def test_memory_stress(self, agent, duration_seconds: int = 60):
        """测试3: 内存压力测试"""
        print(f"\n{'='*80}")
        print(f"💣 测试3: 内存压力测试 ({duration_seconds}秒)")
        print(f"{'='*80}")

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        print(f"   基线内存: {baseline_memory:.1f}MB")

        large_payloads = []

        for i in range(duration_seconds):
            try:
                size = random.randint(1000, 50000)
                payload = {'id': i, 'data': [random.random() for _ in range(size)]}
                agent.submit_task('compute', payload)
                large_payloads.append(payload)

                if (i + 1) % 15 == 0:
                    gc.collect()
                    current_memory = process.memory_info().rss / 1024 / 1024
                    growth = current_memory - baseline_memory
                    print(f"   ⏱️ {i+1}秒: 内存={current_memory:.1f}MB (+{growth:.1f}MB)")

                time.sleep(1)
            except Exception as e:
                print(f"   ❌ 内存测试错误: {str(e)}")

        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory
        print(f"\n   📊 内存压力测试结果: 总增长={total_growth:.1f}MB")
        return True

    def test_system_resilience(self, agent, duration_seconds: int = 120):
        """测试4: 系统韧性测试 - 持续混乱输入"""
        print(f"\n{'='*80}")
        print(f"🛡️ 测试4: 系统韧性测试 - 持续混乱输入 ({duration_seconds}秒)")
        print(f"{'='*80}")

        errors = 0
        healthy_checks = 0
        healthy_count = 0

        for i in range(duration_seconds):
            try:
                if i % 2 == 0:
                    invalid_payloads = [
                        None, '', [], {}, Exception('chaos'),
                        {'circular': None, 'iteration': i}
                    ]
                    payload = random.choice(invalid_payloads)
                    agent.submit_task(random.choice(['compute', 'process', 'analyze']), payload)
                else:
                    normal_payload = {'data': random.random(), 'iteration': i}
                    agent.submit_task(random.choice(['compute', 'process', 'analyze']), normal_payload)

                if (i + 1) % 20 == 0:
                    try:
                        status = agent.get_system_status()
                        health = status['guardian']['overall_status']
                        healthy_checks += 1
                        if health == 'healthy':
                            healthy_count += 1
                        print(f"   ⏱️ {i+1}秒: 健康状态={health} ({healthy_count}/{healthy_checks})")
                    except Exception as e:
                        print(f"   ⚠️ 状态检查失败: {str(e)}")

                time.sleep(1)
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ❌ 韧性测试错误: {str(e)}")

        print(f"\n   📊 系统韧性测试结果: 健康率={healthy_count/healthy_checks*100 if healthy_checks else 0:.1f}%")
        return healthy_count >= healthy_checks * 0.9 if healthy_checks > 0 else True

    def run_tests(self):
        """运行所有深度测试"""
        print("=" * 80)
        print("🔍 快速深度混乱测试")
        print("=" * 80)

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            print("\n📦 初始化Agent...")
            agent = MainLoopController()
            agent.initialize()
            agent.start()
            self.agent = agent

            time.sleep(3)

            results = []
            results.append(("任务提交边界测试", self.test_task_submission_boundary(agent)))
            results.append(("高并发压力测试", self.test_high_concurrency(agent, 60)))
            results.append(("内存压力测试", self.test_memory_stress(agent, 60)))
            results.append(("系统韧性测试", self.test_system_resilience(agent, 120)))

            print("\n" + "=" * 80)
            print("📋 测试结果汇总")
            print("=" * 80)

            for test_name, passed in results:
                status = "✅ 通过" if passed else "❌ 失败"
                print(f"   {test_name}: {status}")

            if self.issues_found:
                print(f"\n🔴 发现的问题 ({len(self.issues_found)}个):")
                for i, issue in enumerate(self.issues_found[:10], 1):
                    print(f"   {i}. {issue}")

            all_passed = all(passed for _, passed in results)
            print("\n" + "=" * 80)
            if all_passed and not self.issues_found:
                print("🎉 所有快速深度混乱测试通过！系统表现良好！")
            else:
                print(f"⚠️  测试完成，发现 {len(self.issues_found)} 个问题")
            print("=" * 80)

            print("\n🛑 停止Agent...")
            agent.stop()
            print("✅ Agent已停止")

            return all_passed and not self.issues_found

        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            traceback.print_exc()
            return False


def main():
    tester = QuickChaosTest()
    success = tester.run_tests()
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
