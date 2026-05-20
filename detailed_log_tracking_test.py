#!/usr/bin/env python3
"""
详细日志跟踪测试 - 慢工出细活
在系统每一句关键代码后面打印日志，验证每个操作是否正常执行

通过超详细日志追踪，发现系统在真实运行时的细微问题
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

sys.path.insert(0, '/workspace')


class DetailedLogTracker:
    """详细日志追踪器"""

    def __init__(self):
        self.log_lines = []
        self._lock = threading.Lock()
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = time.time() - self.start_time
        log_entry = f"[{timestamp:8.3f}s] [{level:8}] {message}"
        with self._lock:
            self.log_lines.append(log_entry)
        print(log_entry)

    def get_logs(self) -> List[str]:
        """获取所有日志"""
        with self._lock:
            return self.log_lines.copy()

    def get_error_count(self) -> int:
        """获取错误日志数量"""
        with self._lock:
            return sum(1 for log in self.log_lines if '[ERROR]' in log or '[CRITICAL]' in log)

    def get_warning_count(self) -> int:
        """获取警告日志数量"""
        with self._lock:
            return sum(1 for log in self.log_lines if '[WARNING]' in log)


class DetailedChaosTest:
    """详细日志跟踪混沌测试"""

    def __init__(self):
        self.tracker = DetailedLogTracker()
        self.agent = None

    def test_agent_lifecycle_with_detailed_logging(self):
        """测试1: Agent生命周期详细日志跟踪"""
        print("=" * 80)
        print("🔍 测试1: Agent生命周期详细日志跟踪")
        print("=" * 80)

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            self.tracker.log("开始初始化Agent")

            self.tracker.log("创建MainLoopController实例")
            agent = MainLoopController()

            self.tracker.log("调用initialize()方法")
            agent.initialize()

            self.tracker.log("调用start()方法")
            agent.start()

            self.tracker.log("Agent已启动，等待10秒...")
            time.sleep(10)

            self.tracker.log("检查系统状态 - 第1次")
            status1 = agent.get_system_status()
            self.tracker.log(f"状态检查结果: {status1.get('guardian', {}).get('overall_status', 'unknown')}")

            self.tracker.log("提交测试任务1")
            task_id1 = agent.submit_task('compute', {'test': 1})
            self.tracker.log(f"任务1已提交: {task_id1}")

            self.tracker.log("提交测试任务2")
            task_id2 = agent.submit_task('process', {'test': 2})
            self.tracker.log(f"任务2已提交: {task_id2}")

            self.tracker.log("提交测试任务3")
            task_id3 = agent.submit_task('analyze', {'test': 3})
            self.tracker.log(f"任务3已提交: {task_id3}")

            self.tracker.log("等待5秒让任务执行...")
            time.sleep(5)

            self.tracker.log("检查系统状态 - 第2次")
            status2 = agent.get_system_status()
            self.tracker.log(f"状态检查结果: {status2.get('guardian', {}).get('overall_status', 'unknown')}")

            self.tracker.log("获取执行摘要")
            exec_summary = status2.get('execution', {})
            self.tracker.log(f"执行摘要: 运行中={exec_summary.get('running_tasks', 0)}, "
                           f"已完成={exec_summary.get('completed_tasks', 0)}, "
                           f"待处理={exec_summary.get('pending_tasks', 0)}")

            self.tracker.log("停止Agent")
            agent.stop()

            self.tracker.log("Agent已停止，测试完成")

            return True

        except Exception as e:
            self.tracker.log(f"[CRITICAL] 测试失败: {str(e)}", "CRITICAL")
            self.tracker.log(f"[CRITICAL] 详细错误: {traceback.format_exc()}", "CRITICAL")
            return False

    def test_high_frequency_task_submission(self, duration_seconds: int = 300):
        """测试2: 高频任务提交详细日志跟踪"""
        print("\n" + "=" * 80)
        print(f"⚡ 测试2: 高频任务提交详细日志跟踪 ({duration_seconds}秒)")
        print("=" * 80)

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            self.tracker.log("初始化Agent")
            agent = MainLoopController()
            agent.initialize()
            agent.start()

            self.tracker.log("Agent已启动，等待5秒稳定...")
            time.sleep(5)

            self.tracker.log("开始高频任务提交测试")
            tasks_submitted = 0
            errors = 0
            checkpoint_interval = 30

            for i in range(duration_seconds):
                try:
                    num_tasks = random.randint(1, 20)

                    for j in range(num_tasks):
                        task_type = random.choice(['compute', 'process', 'analyze'])
                        payload = {
                            'iteration': i,
                            'batch': j,
                            'data': [random.random() for _ in range(10)]
                        }

                        task_id = agent.submit_task(task_type, payload)
                        tasks_submitted += 1

                    if (i + 1) % 10 == 0:
                        self.tracker.log(f"[{i+1}秒] 已提交{tasks_submitted}个任务")

                    if (i + 1) % checkpoint_interval == 0:
                        self.tracker.log(f"[检查点 {i+1}秒] 获取系统状态")
                        status = agent.get_system_status()
                        health = status.get('guardian', {}).get('overall_status', 'unknown')
                        exec_summary = status.get('execution', {})
                        self.tracker.log(f"[检查点 {i+1}秒] 健康状态: {health}, "
                                       f"运行: {exec_summary.get('running_tasks', 0)}, "
                                       f"完成: {exec_summary.get('completed_tasks', 0)}")

                        if health != 'healthy':
                            self.tracker.log(f"[WARNING] 系统健康状态异常: {health}", "WARNING")

                    time.sleep(1)

                except Exception as e:
                    errors += 1
                    self.tracker.log(f"[ERROR] 第{i}秒任务提交错误: {str(e)}", "ERROR")
                    if errors <= 5:
                        self.tracker.log(f"[ERROR] 错误追踪: {traceback.format_exc()}", "ERROR")

            self.tracker.log(f"高频测试完成: 提交{tasks_submitted}个任务, 发生{errors}个错误")

            self.tracker.log("停止Agent")
            agent.stop()

            return errors < tasks_submitted * 0.1

        except Exception as e:
            self.tracker.log(f"[CRITICAL] 测试失败: {str(e)}", "CRITICAL")
            self.tracker.log(f"[CRITICAL] 详细错误: {traceback.format_exc()}", "CRITICAL")
            return False

    def test_concurrent_chaos_simulation(self, duration_seconds: int = 300):
        """测试3: 并发混沌模拟详细日志"""
        print("\n" + "=" * 80)
        print(f"🌪️ 测试3: 并发混沌模拟详细日志 ({duration_seconds}秒)")
        print("=" * 80)

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            self.tracker.log("初始化Agent")
            agent = MainLoopController()
            agent.initialize()
            agent.start()

            self.tracker.log("Agent已启动，等待3秒稳定...")
            time.sleep(3)

            workers = []
            num_workers = 50

            def chaos_worker(worker_id: int):
                self.tracker.log(f"Worker-{worker_id} 开始工作")
                tasks_this_worker = 0

                for i in range(50):
                    try:
                        task_type = random.choice(['compute', 'process', 'analyze', 'default'])
                        payload = {
                            'worker_id': worker_id,
                            'iteration': i,
                            'chaos': True,
                            'data': [random.random() for _ in range(20)]
                        }

                        task_id = agent.submit_task(task_type, payload)
                        tasks_this_worker += 1

                        if i % 10 == 0:
                            self.tracker.log(f"Worker-{worker_id} 已提交{i+1}个任务")

                        time.sleep(random.uniform(0.01, 0.1))

                    except Exception as e:
                        self.tracker.log(f"[ERROR] Worker-{worker_id} 第{i}次提交失败: {str(e)}", "ERROR")

                self.tracker.log(f"Worker-{worker_id} 完成工作，共提交{tasks_this_worker}个任务")

            self.tracker.log(f"启动{num_workers}个并发混沌工作线程")

            for i in range(num_workers):
                t = threading.Thread(target=chaos_worker, args=(i,), daemon=True)
                workers.append(t)
                t.start()

            self.tracker.log("所有工作线程已启动")

            checkpoint_interval = 30
            for i in range(duration_seconds):
                time.sleep(1)

                if (i + 1) % checkpoint_interval == 0:
                    try:
                        status = agent.get_system_status()
                        health = status.get('guardian', {}).get('overall_status', 'unknown')
                        exec_summary = status.get('execution', {})
                        self.tracker.log(f"[检查点 {i+1}秒] 健康: {health}, "
                                       f"运行: {exec_summary.get('running_tasks', 0)}, "
                                       f"完成: {exec_summary.get('completed_tasks', 0)}, "
                                       f"待处理: {exec_summary.get('pending_tasks', 0)}")

                        if health != 'healthy':
                            self.tracker.log(f"[WARNING] 系统状态异常: {health}", "WARNING")

                    except Exception as e:
                        self.tracker.log(f"[ERROR] 检查点{i+1}秒状态获取失败: {str(e)}", "ERROR")

            self.tracker.log("等待所有工作线程完成")
            for t in workers:
                t.join(timeout=5)

            self.tracker.log("停止Agent")
            agent.stop()

            return True

        except Exception as e:
            self.tracker.log(f"[CRITICAL] 测试失败: {str(e)}", "CRITICAL")
            self.tracker.log(f"[CRITICAL] 详细错误: {traceback.format_exc()}", "CRITICAL")
            return False

    def test_memory_stress_with_logging(self, duration_seconds: int = 180):
        """测试4: 内存压力测试与日志"""
        print("\n" + "=" * 80)
        print(f"💣 测试4: 内存压力测试与日志 ({duration_seconds}秒)")
        print("=" * 80)

        try:
            from main_loop_controller_orchestrator_system import MainLoopController

            self.tracker.log("初始化Agent")
            agent = MainLoopController()
            agent.initialize()
            agent.start()

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024

            self.tracker.log(f"基线内存: {baseline_memory:.2f}MB")
            time.sleep(2)

            large_objects = []

            for i in range(duration_seconds):
                try:
                    size = random.randint(1000, 50000)
                    payload = {
                        'id': i,
                        'data': [random.random() for _ in range(size)]
                    }

                    task_id = agent.submit_task('compute', payload)
                    large_objects.append(payload)

                    if (i + 1) % 15 == 0:
                        gc.collect()
                        current_memory = process.memory_info().rss / 1024 / 1024
                        growth = current_memory - baseline_memory
                        self.tracker.log(f"[内存检查 {i+1}秒] "
                                       f"当前: {current_memory:.1f}MB, "
                                       f"增长: +{growth:.1f}MB, "
                                       f"对象数: {len(large_objects)}")

                        if growth > 500:
                            self.tracker.log(f"[WARNING] 内存增长过大: +{growth:.1f}MB", "WARNING")

                    time.sleep(1)

                except Exception as e:
                    self.tracker.log(f"[ERROR] 第{i}秒内存测试错误: {str(e)}", "ERROR")

            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            total_growth = final_memory - baseline_memory

            self.tracker.log(f"内存压力测试完成")
            self.tracker.log(f"最终内存: {final_memory:.2f}MB")
            self.tracker.log(f"总增长: +{total_growth:.2f}MB")

            self.tracker.log("停止Agent")
            agent.stop()

            return True

        except Exception as e:
            self.tracker.log(f"[CRITICAL] 测试失败: {str(e)}", "CRITICAL")
            self.tracker.log(f"[CRITICAL] 详细错误: {traceback.format_exc()}", "CRITICAL")
            return False

    def analyze_logs(self):
        """分析日志输出"""
        print("\n" + "=" * 80)
        print("📊 日志分析报告")
        print("=" * 80)

        logs = self.tracker.get_logs()
        total_logs = len(logs)
        error_count = self.tracker.get_error_count()
        warning_count = self.tracker.get_warning_count()

        print(f"总日志条数: {total_logs}")
        print(f"错误日志: {error_count}")
        print(f"警告日志: {warning_count}")
        print(f"成功率: {((total_logs - error_count) / total_logs * 100):.2f}%")

        if logs:
            print("\n最近20条日志:")
            for log in logs[-20:]:
                print(f"  {log}")

        print("\n" + "=" * 80)
        if error_count == 0:
            print("✅ 系统运行完美，无错误！")
        elif error_count < total_logs * 0.01:
            print("⚠️  系统运行良好，错误率极低")
        else:
            print(f"❌ 发现 {error_count} 个错误，需要检查")
        print("=" * 80)

    def run_all_tests(self):
        """运行所有详细日志测试"""
        print("=" * 80)
        print("🔍 详细日志跟踪混沌测试 - 慢工出细活")
        print("=" * 80)
        print("通过超详细日志追踪每个代码执行，验证系统稳定性")

        results = []

        # 测试1: Agent生命周期测试（短）
        print("\n开始测试1: Agent生命周期测试（60秒）...")
        results.append(("Agent生命周期", self.test_agent_lifecycle_with_detailed_logging()))

        # 测试2: 高频任务提交（5分钟）
        print("\n开始测试2: 高频任务提交测试（5分钟）...")
        results.append(("高频任务提交", self.test_high_frequency_task_submission(300)))

        # 测试3: 并发混沌模拟（5分钟）
        print("\n开始测试3: 并发混沌模拟测试（5分钟）...")
        results.append(("并发混沌模拟", self.test_concurrent_chaos_simulation(300)))

        # 测试4: 内存压力测试（3分钟）
        print("\n开始测试4: 内存压力测试（3分钟）...")
        results.append(("内存压力测试", self.test_memory_stress_with_logging(180)))

        # 分析日志
        self.analyze_logs()

        # 打印结果汇总
        print("\n" + "=" * 80)
        print("📋 测试结果汇总")
        print("=" * 80)

        for test_name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"   {test_name}: {status}")

        all_passed = all(passed for _, passed in results)
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 所有详细日志跟踪测试通过！")
        else:
            failed_tests = [name for name, passed in results if not passed]
            print(f"⚠️  {len(failed_tests)}个测试失败")
        print("=" * 80)


def main():
    tester = DetailedChaosTest()
    tester.run_all_tests()


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
